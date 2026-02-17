"""Tests for CSV injection protection."""


from paper_scraper.core.csv_utils import sanitize_csv_field


class TestSanitizeCsvField:
    """Tests for sanitize_csv_field."""

    def test_normal_value_unchanged(self):
        assert sanitize_csv_field("Hello World") == "Hello World"

    def test_empty_string_unchanged(self):
        assert sanitize_csv_field("") == ""

    def test_equals_prefix(self):
        assert sanitize_csv_field("=1+2") == "'=1+2"

    def test_plus_prefix(self):
        assert sanitize_csv_field("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"

    def test_minus_prefix(self):
        assert sanitize_csv_field("-1+2") == "'-1+2"

    def test_at_prefix(self):
        assert sanitize_csv_field("@SUM(A1:A2)") == "'@SUM(A1:A2)"

    def test_tab_prefix(self):
        assert sanitize_csv_field("\tcmd") == "'\tcmd"

    def test_carriage_return_replaced(self):
        # \r is replaced with space, result no longer starts with dangerous char
        assert sanitize_csv_field("\rcmd") == " cmd"

    def test_pipe_prefix(self):
        assert sanitize_csv_field("|cmd") == "'|cmd"

    def test_embedded_newline_stripped(self):
        assert sanitize_csv_field("safe\n=cmd") == "safe =cmd"

    def test_embedded_crlf_stripped(self):
        assert sanitize_csv_field("safe\r\n=cmd") == "safe =cmd"

    def test_embedded_cr_stripped(self):
        assert sanitize_csv_field("safe\r=cmd") == "safe =cmd"

    def test_number_unchanged(self):
        assert sanitize_csv_field("42") == "42"

    def test_doi_unchanged(self):
        assert sanitize_csv_field("10.1234/abc") == "10.1234/abc"

    def test_url_unchanged(self):
        assert sanitize_csv_field("https://example.com") == "https://example.com"
