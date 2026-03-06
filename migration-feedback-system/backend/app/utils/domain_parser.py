def extract_domain(email: str) -> str:
    """Extract the domain portion of an email address."""
    if "@" in email:
        return email.split("@", 1)[1].lower().strip()
    return email.lower().strip()


def is_internal_email(email: str, internal_domain: str) -> bool:
    """Check whether an email belongs to the internal organization."""
    domain = extract_domain(email)
    return domain == internal_domain.lower().strip()
