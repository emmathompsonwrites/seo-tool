"""Email validation — extracted verbatim from RankKW's chunk (function `ly`)."""

DISPOSABLE_DOMAINS: set[str] = {
    "mailinator.com", "guerrillamail.com", "guerrillamailblock.com",
    "sharklasers.com", "10minutemail.com", "10minutemail.net",
    "tempmail.com", "temp-mail.org", "tempmailo.com", "tempr.email",
    "throwawaymail.com", "yopmail.com", "getnada.com", "nada.email",
    "trashmail.com", "trashmail.de", "maildrop.cc", "mailcatch.com",
    "dispostable.com", "fakeinbox.com", "mailnesia.com", "mohmal.com",
    "emailondeck.com", "tempinbox.com", "spamgourmet.com",
    "mytemp.email", "moakt.com", "discard.email", "1secmail.com",
    "mailtemp.info", "inboxkitten.com", "burnermail.io",
    "mintemail.com", "spam4.me", "grr.la", "einrot.com",
    "tmail.ws", "tmails.net", "harakirimail.com",
}


def is_valid_email_domain(email: str) -> bool:
    """
    Mirror of RankKW's `ly(e)`:

        let t = e.trim().toLowerCase().split("@")[1] ?? "";
        return !!t && !!t.includes(".") && !lh.some(d => t === d || t.endsWith("." + d));

    Rules:
      1. Must have a domain part (something after @).
      2. Domain must contain a dot.
      3. Domain must not be exactly a blocked domain.
      4. Domain must not end with ".<blocked>" (subdomain of a blocked domain).
    """
    try:
        domain = email.strip().lower().rsplit("@", 1)[1]
    except (IndexError, AttributeError):
        return False

    if not domain or "." not in domain:
        return False

    for blocked in DISPOSABLE_DOMAINS:
        if domain == blocked or domain.endswith("." + blocked):
            return False
    return True