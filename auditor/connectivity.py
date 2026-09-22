"""Small, failure-safe connectivity probe for optional audit synchronization."""

from urllib.error import URLError
from urllib.request import Request, urlopen


def is_internet_available(timeout_seconds: float = 0.75) -> bool:
    """Return whether a lightweight external request succeeds, never raising.

    This probe is deliberately independent of lifecycle calculations: a failed
    probe only postpones synchronization, not local sustainability auditing.
    """
    try:
        request = Request("https://www.google.com/generate_204", method="HEAD")
        with urlopen(request, timeout=timeout_seconds) as response:
            return 200 <= response.status < 400
    except (OSError, URLError, ValueError):
        return False
