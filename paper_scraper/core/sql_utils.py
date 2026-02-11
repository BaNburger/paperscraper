"""SQL utility functions for query building and parameter escaping."""


def escape_like(text: str) -> str:
    """Escape special characters for SQL LIKE patterns.

    This function escapes the wildcard characters used in SQL LIKE clauses:
    - Backslash (\) - Used as the escape character itself
    - Percent (%) - Matches any sequence of zero or more characters
    - Underscore (_) - Matches any single character

    Args:
        text: The search text to escape.

    Returns:
        Text with LIKE special characters properly escaped.

    Example:
        >>> escape_like("test_file%.txt")
        'test\\_file\\%.txt'
    """
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
