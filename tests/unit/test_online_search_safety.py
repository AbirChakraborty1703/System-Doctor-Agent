from packages.schemas import DeviceMetadata, OSType, TroubleshootingSession
from packages.shared_utils.config import get_config
from packages.shared_utils.online_search import OnlineSearchClient


def test_online_search_returns_empty_when_disabled() -> None:
    client = OnlineSearchClient(get_config())
    session = TroubleshootingSession(
        user_issue="Windows update fails with error code",
        metadata=DeviceMetadata(os=OSType.WINDOWS, online_search_enabled=False),
    )

    results = client.search(session, enabled=False)
    assert results == []


def test_online_search_domain_filter_accepts_trusted_sources() -> None:
    client = OnlineSearchClient(get_config())

    assert client._is_trusted_domain("https://support.microsoft.com/help/123")
    assert not client._is_trusted_domain("https://random-untrusted-example.invalid/article")
