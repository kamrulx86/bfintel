from datetime import datetime, timezone

from app.core.abuse_report_config import AbuseReportSettings, get_abuse_report_settings
from app.schemas.investigation import IpInvestigationProfile


def _fmt_ts(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_brute_force_report(
    profile: IpInvestigationProfile,
    settings: AbuseReportSettings | None = None,
) -> tuple[str, str, str | None, str | None]:
    """Returns subject, body, isp_name, asn."""
    cfg = settings or get_abuse_report_settings()
    geo = profile.geo
    isp = (geo.isp if geo else None) or (geo.organization_name if geo else None)
    asn = geo.asn if geo else None

    subject = f"Abuse report: authentication brute force from {profile.source_ip}"

    lines = [
        "Dear Abuse Team,",
        "",
        f"We are reporting abusive authentication activity originating from {profile.source_ip}.",
        "",
        "Reporter",
        f"  Organization: {cfg.reporter_org_name}",
        f"  Contact email: {cfg.reporter_email}",
    ]
    if cfg.reporter_phone:
        lines.append(f"  Contact phone: {cfg.reporter_phone}")
    lines.extend(
        [
            "",
            "Offending IP",
            f"  Address: {profile.source_ip}",
            f"  Network scope: {profile.network_scope}",
        ]
    )
    if geo:
        loc = ", ".join(x for x in [geo.city, geo.region, geo.country_name] if x)
        if loc:
            lines.append(f"  Location (GeoIP): {loc}")
        if isp:
            lines.append(f"  ISP / org: {isp}")
        if asn:
            lines.append(f"  ASN: {asn}")
        if geo.reverse_dns:
            lines.append(f"  Reverse DNS: {geo.reverse_dns}")

    lines.extend(
        [
            "",
            "Activity summary (observed in our environment)",
            f"  First seen: {_fmt_ts(profile.first_seen)}",
            f"  Last seen: {_fmt_ts(profile.last_seen)}",
            f"  Total authentication events: {profile.total_events}",
            f"  Failed attempts: {profile.failure_count}",
            f"  Successful logins (if any): {profile.success_count}",
            f"  Correlated attack sessions: {profile.session_count}",
            f"  Risk assessment: {profile.max_risk_level} (score {profile.max_risk_score}/100)",
        ]
    )
    if profile.services:
        lines.append(f"  Services targeted: {', '.join(profile.services)}")
    if profile.target_hosts:
        lines.append(f"  Target hosts: {', '.join(profile.target_hosts[:20])}")
    if profile.usernames:
        sample = profile.usernames[:15]
        suffix = " (sample)" if len(profile.usernames) > len(sample) else ""
        lines.append(f"  Usernames attempted{suffix}: {', '.join(sample)}")

    if profile.risk_reasons:
        lines.append("")
        lines.append("Risk indicators")
        for reason in profile.risk_reasons[:12]:
            lines.append(f"  - {reason}")

    for snap in profile.threat_intel:
        if snap.provider == "abuseipdb" and snap.success:
            score = snap.data.get("abuse_confidence_score")
            reports = snap.data.get("total_reports")
            lines.append("")
            lines.append("Third-party intelligence (AbuseIPDB)")
            lines.append(f"  Community abuse confidence: {score}")
            lines.append(f"  Total community reports: {reports}")
            break

    lines.extend(
        [
            "",
            "Requested action",
            "  Please investigate and take appropriate action against this source, including suspension",
            "  or filtering if it violates your acceptable use policy.",
            "",
            "This report was generated from correlated Wazuh SIEM alerts and BFIntel investigation data.",
            "",
            "Regards,",
            cfg.reporter_org_name,
        ]
    )

    return subject, "\n".join(lines), isp, asn
