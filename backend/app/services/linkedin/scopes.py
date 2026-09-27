import re
from urllib.parse import unquote_plus


def parse_linkedin_scopes(value: str) -> set[str]:
    """Normalize OAuth scope strings returned as spaces, commas, or URL-encoded text."""
    return {scope for scope in re.split(r"[\s,]+", unquote_plus(value).strip()) if scope}
