"""Testy renderowania tekstu czatu do HTML (utils/chat_render.py)."""

from utils.chat_render import to_html


class TestEscaping:
    def test_escapes_html(self):
        assert "<script>" not in to_html("<script>alert(1)</script>")
        assert "&lt;script&gt;" in to_html("<script>x</script>")

    def test_empty(self):
        assert to_html("") == ""


class TestLinks:
    def test_https_url_clickable(self):
        out = to_html("Zobacz https://youtu.be/abc123 teraz")
        assert '<a href="https://youtu.be/abc123">https://youtu.be/abc123</a>' in out

    def test_www_gets_https_prefix(self):
        out = to_html("wejdz na www.example.com/x")
        assert 'href="https://www.example.com/x"' in out

    def test_youtu_be_bare_clickable(self):
        out = to_html("link youtu.be/XYZ_1")
        assert 'href="https://youtu.be/XYZ_1"' in out

    def test_trailing_punctuation_not_in_link(self):
        out = to_html("otworz https://youtu.be/abc.")
        assert 'href="https://youtu.be/abc"' in out


class TestTitleLinks:
    def test_title_becomes_link(self):
        out = to_html(
            "Polecam film Rust vs Go bardzo",
            title_urls={"Rust vs Go": "https://youtu.be/r1"},
        )
        assert '<a href="https://youtu.be/r1">Rust vs Go</a>' in out

    def test_only_first_occurrence(self):
        out = to_html(
            "Rust vs Go oraz Rust vs Go",
            title_urls={"Rust vs Go": "https://youtu.be/r1"},
        )
        assert out.count('<a href="https://youtu.be/r1">') == 1

    def test_short_title_ignored(self):
        out = to_html("abc", title_urls={"abc": "https://youtu.be/x"})
        assert "<a" not in out

    def test_longer_title_wins(self):
        urls = {
            "Python": "https://youtu.be/py",
            "Python dla poczatkujacych": "https://youtu.be/pyx",
        }
        out = to_html("Kurs Python dla poczatkujacych super", title_urls=urls)
        assert 'href="https://youtu.be/pyx"' in out
        assert 'href="https://youtu.be/py"' not in out


class TestMarkdown:
    def test_bold(self):
        assert "<b>ważne</b>" in to_html("to **ważne** slowo")

    def test_italic_star(self):
        assert "<i>kursywa</i>" in to_html("to *kursywa* tu")

    def test_italic_underscore(self):
        assert "<i>emfaza</i>" in to_html("to _emfaza_ tu")

    def test_inline_code(self):
        assert "<code>ollama pull</code>" in to_html("uruchom `ollama pull`")

    def test_code_not_formatted_inside(self):
        out = to_html("`**nie bold**`")
        assert "<b>" not in out
        assert "<code>**nie bold**</code>" in out

    def test_bullet_list(self):
        out = to_html("- pierwszy\n- drugi")
        assert "<ul" in out and out.count("<li>") == 2

    def test_numbered_list(self):
        out = to_html("1. raz\n2. dwa")
        assert "<ol" in out and out.count("<li>") == 2

    def test_newlines_become_br(self):
        out = to_html("linia1\nlinia2")
        assert "<br>" in out


class TestCombined:
    def test_bold_link_and_title(self):
        out = to_html(
            "**Polecam** Rust vs Go: https://youtu.be/r1",
            title_urls={"Rust vs Go": "https://youtu.be/r1"},
        )
        assert "<b>Polecam</b>" in out
        assert '<a href="https://youtu.be/r1">Rust vs Go</a>' in out
        assert '<a href="https://youtu.be/r1">https://youtu.be/r1</a>' in out
