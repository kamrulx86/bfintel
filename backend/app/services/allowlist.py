import ipaddress

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ip_lists import AllowlistEntry


def is_ip_allowlisted(db: Session, organization_id, source_ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(source_ip)
    except ValueError:
        return False

    entries = db.scalars(
        select(AllowlistEntry).where(AllowlistEntry.organization_id == organization_id)
    ).all()
    for entry in entries:
        if entry.entry_type == "ip" and entry.value == source_ip:
            return True
        if entry.entry_type == "cidr":
            try:
                network = ipaddress.ip_network(entry.value, strict=False)
                if addr in network:
                    return True
            except ValueError:
                continue
    return False
