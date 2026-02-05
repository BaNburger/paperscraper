"""CSV export utilities with injection protection."""

_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "|")


def sanitize_csv_field(value: str) -> str:
    """Prefix dangerous characters to prevent formula injection.

    Spreadsheet applications may execute cell values starting with
    ``=``, ``+``, ``-``, ``@``, ``\\t``, ``\\r``, or ``|`` as formulas
    or DDE commands.  Prefixing such values with a single quote
    neutralises this.  Embedded newlines are also replaced to prevent
    injection on subsequent CSV lines.

    Args:
        value: The raw field value.

    Returns:
        A sanitized string safe for CSV export.
    """
    if not value:
        return value
    # Strip embedded newlines that could start a new CSV row with a formula
    value = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    if value[0] in _DANGEROUS_PREFIXES:
        return f"'{value}"
    return value
