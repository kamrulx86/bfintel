from datetime import datetime, timezone

from app.core.abuse_report_config import AbuseReportSettings
from app.schemas.intel import GeoIntelOut
from app.schemas.investigation import IpInvestigationProfile
from app.services.abuse_report_builder import build_brute_force_report


def test_build_report_includes_ip_and_stats():
    profile = IpInvestigationProfile(
        source_ip="203.0.113.55",
        network_scope="public",
        first_seen=datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc),
        last_seen=datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc),
        total_events=42,
        failure_count=40,
        success_count=2,
        session_count=3,
        max_risk_score=80,
        max_risk_level="high",
        target_hosts=["bastion.example.com"],
        services=["ssh"],
        usernames=["root", "admin"],
        risk_reasons=["High volume of failed SSH logins"],
        geo=GeoIntelOut(
            country_code="US",
            country_name="United States",
            region="CA",
            city="Los Angeles",
            latitude=None,
            longitude=None,
            asn="AS12345",
            isp="Example ISP",
            organization_name="Example Net",
            reverse_dns="host.example.net",
            is_hosting=False,
            network_scope="public",
            last_enriched_at=None,
            enrichment_status="ok",
        ),
    )
    settings = AbuseReportSettings.model_construct(
        reporter_org_name="Acme SOC",
        reporter_email="soc@acme.test",
        reporter_phone=None,
    )
    subject, body, isp, asn = build_brute_force_report(profile, settings=settings)
    assert "203.0.113.55" in subject
    assert "203.0.113.55" in body
    assert "Acme SOC" in body
    assert "Example ISP" in body
    assert isp == "Example ISP"
    assert asn == "AS12345"
    assert "bastion.example.com" in body
