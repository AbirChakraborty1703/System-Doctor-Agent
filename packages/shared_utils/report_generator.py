"""Session report generation utilities."""

from __future__ import annotations

from typing import List

from packages.schemas import SessionReport, TroubleshootingSession


def build_session_report(session: TroubleshootingSession) -> SessionReport:
    result = "Resolved" if session.status.value == "resolved" else "Unresolved"
    if session.status.value == "escalated":
        result = "Escalated"

    fixes_attempted: List[str] = []
    if session.remediation:
        for step in session.remediation.steps:
            fixes_attempted.append(step.action)

    escalation = session.escalation_advice or "No escalation needed at this time."
    return SessionReport(
        session_id=session.session_id,
        issue_summary=session.user_issue,
        os=session.metadata.os,
        diagnosis=session.diagnoses,
        online_insights=session.online_insights,
        fixes_attempted=fixes_attempted,
        result=result,
        escalation_advice=escalation,
    )


def report_to_markdown(report: SessionReport) -> str:
    lines = [
        "# SystemDoctor AI Session Report",
        "",
        f"- Session ID: {report.session_id}",
        f"- Generated At: {report.generated_at.isoformat()}",
        f"- OS: {report.os.value}",
        f"- Issue: {report.issue_summary}",
        f"- Result: {report.result}",
        "",
        "## Top Diagnoses",
    ]

    if not report.diagnosis:
        lines.append("No diagnosis available.")
    else:
        for item in report.diagnosis:
            lines.append(
                f"- {item.title} ({item.confidence:.0%}) | category={item.category.value}"
            )

    lines.append("")
    lines.append("## Online Insights")
    if not report.online_insights:
        lines.append("No online insight enrichment used.")
    else:
        for item in report.online_insights[:5]:
            lines.append(f"- {item.title} ({item.source})")
            lines.append(f"  {item.summary}")
            lines.append(f"  {item.url}")

    lines.append("")
    lines.append("## Fixes Attempted")
    if not report.fixes_attempted:
        lines.append("No fixes attempted.")
    else:
        lines.extend([f"- {fix}" for fix in report.fixes_attempted])

    lines.append("")
    lines.append("## Escalation Advice")
    lines.append(report.escalation_advice)

    return "\n".join(lines)
