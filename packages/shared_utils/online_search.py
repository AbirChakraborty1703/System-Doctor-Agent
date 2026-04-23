"""Safe online troubleshooting enrichment via allowlisted sources."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

from packages.schemas import OnlineInsight, OSType, TroubleshootingSession

from .config import AppConfig
from .logger import get_logger
from .text_utils import tokenize


@dataclass(frozen=True)
class _ResultRow:
    title: str
    url: str
    summary: str


class OnlineSearchClient:
    """Performs tightly scoped online search with safe source filtering."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._logger = get_logger("systemdoctor.online_search")

    def search(self, session: TroubleshootingSession, enabled: bool) -> List[OnlineInsight]:
        if not enabled:
            return []

        queries = self._build_queries(session)
        if not queries:
            return []

        all_rows: List[_ResultRow] = []
        seen_urls: set[str] = set()

        for query in queries:
            for row in self._query_duckduckgo(query):
                if row.url in seen_urls:
                    continue
                seen_urls.add(row.url)
                all_rows.append(row)
                if len(all_rows) >= self._config.online_search_max_results:
                    break
            if len(all_rows) >= self._config.online_search_max_results:
                break

        return [
            OnlineInsight(
                title=row.title,
                url=row.url,
                source=urlparse(row.url).netloc,
                summary=row.summary,
                relevance=self._relevance(session, row),
            )
            for row in sorted(all_rows, key=lambda item: self._relevance(session, item), reverse=True)
        ]

    def _build_queries(self, session: TroubleshootingSession) -> List[str]:
        base_issue = session.user_issue.strip()
        os_hint = session.metadata.os.value if session.metadata.os != OSType.UNKNOWN else ""
        model_hint = session.metadata.device_model or ""

        queries: List[str] = [base_issue]
        if os_hint:
            queries.append(f"{os_hint} {base_issue}")

        if session.metadata.recent_update:
            queries.append(
                f"{os_hint} update known issues {session.metadata.recent_update} {model_hint}".strip()
            )

        if session.metadata.error_message:
            queries.append(f"{os_hint} error {session.metadata.error_message}")

        if session.triage and session.triage.category.value in {"update_driver", "bios_boot", "network"}:
            queries.append(f"{os_hint} {session.triage.category.value} troubleshooting known fix")

        deduped: List[str] = []
        seen: set[str] = set()
        for query in queries:
            normalized = " ".join(query.split()).strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(query.strip())
        return deduped

    def _query_duckduckgo(self, query: str) -> List[_ResultRow]:
        endpoint = (
            "https://api.duckduckgo.com/?format=json&no_html=1&no_redirect=1&q="
            f"{quote_plus(query)}"
        )

        try:
            request = Request(
                endpoint,
                headers={"User-Agent": "SystemDoctorAI/1.0"},
            )
            with urlopen(request, timeout=self._config.online_search_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:
            self._logger.warning("online search failed for query=%s error=%s", query, exc)
            return []

        rows: List[_ResultRow] = []
        rows.extend(self._extract_primary(payload))
        rows.extend(self._extract_related(payload))

        filtered: List[_ResultRow] = []
        for row in rows:
            if self._is_trusted_domain(row.url):
                filtered.append(row)
        return filtered

    def _extract_primary(self, payload: Dict[str, object]) -> List[_ResultRow]:
        abstract_text = str(payload.get("AbstractText") or "").strip()
        abstract_url = str(payload.get("AbstractURL") or "").strip()
        heading = str(payload.get("Heading") or "").strip()

        if not abstract_text or not abstract_url:
            return []

        return [
            _ResultRow(
                title=heading or "Troubleshooting reference",
                url=abstract_url,
                summary=abstract_text[:320],
            )
        ]

    def _extract_related(self, payload: Dict[str, object]) -> List[_ResultRow]:
        rows: List[_ResultRow] = []
        topics = payload.get("RelatedTopics")
        if not isinstance(topics, list):
            return rows

        for topic in topics:
            if isinstance(topic, dict) and "Topics" in topic:
                nested = topic.get("Topics")
                if isinstance(nested, list):
                    rows.extend(self._extract_topic_rows(nested))
                continue
            if isinstance(topic, dict):
                rows.extend(self._extract_topic_rows([topic]))

        return rows

    @staticmethod
    def _extract_topic_rows(topics: List[Dict[str, object]]) -> List[_ResultRow]:
        rows: List[_ResultRow] = []
        for item in topics:
            url = str(item.get("FirstURL") or "").strip()
            text = str(item.get("Text") or "").strip()
            if not url or not text:
                continue
            title = text.split(" - ", 1)[0].strip()
            rows.append(_ResultRow(title=title, url=url, summary=text[:320]))
        return rows

    def _is_trusted_domain(self, url: str) -> bool:
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            return False

        for trusted in self._config.online_search_trusted_domains:
            if domain == trusted or domain.endswith(f".{trusted}"):
                return True
        return False

    @staticmethod
    def _relevance(session: TroubleshootingSession, row: _ResultRow) -> float:
        issue_tokens = set(tokenize(session.user_issue))
        text_tokens = set(tokenize(f"{row.title} {row.summary}"))
        if not issue_tokens:
            return 0.0
        overlap = issue_tokens.intersection(text_tokens)
        return round(min(1.0, len(overlap) / max(len(issue_tokens), 1)), 4)
