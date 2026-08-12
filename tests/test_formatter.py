import pytest

from linkedin_cli.formatter import LITTLE_TEXT_RESERVED, escape_little_text


@pytest.mark.parametrize(
    "char",
    ["|", "{", "}", "@", "[", "]", "(", ")", "<", ">", "*", "_", "~"],
)
def test_reserved_char_escaped(char):
    assert escape_little_text(char) == "\\" + char


def test_double_quote_not_escaped():
    assert escape_little_text('say "hi"') == 'say "hi"'


def test_backslash_escaped():
    assert escape_little_text("a\\b") == "a\\\\b"


def test_plain_text_unchanged():
    assert escape_little_text("Hello, LinkedIn!") == "Hello, LinkedIn!"


def test_parens_escaped_to_avoid_truncation():
    assert escape_little_text("see (this part)") == "see \\(this part\\)"


def test_newlines_and_emoji_kept():
    text = "linha 1\n\n📦 pacote 🦪"
    assert escape_little_text(text) == text


def test_hashtag_preserved_at_start():
    assert escape_little_text("#Shelloma") == "#Shelloma"


def test_hashtag_preserved_after_space():
    assert escape_little_text("vamos ver #Ollama local") == "vamos ver #Ollama local"


def test_hashtag_preserved_after_newline():
    assert escape_little_text("\n#Terminal") == "\n#Terminal"


def test_hash_mid_word_escaped():
    assert escape_little_text("linguagem C#") == "linguagem C\\#"


def test_hash_followed_by_space_escaped():
    assert escape_little_text("tag # aqui") == "tag \\# aqui"


def test_hash_alone_escaped():
    assert escape_little_text("#") == "\\#"


def test_hashtag_not_split():
    assert escape_little_text("#GoLang #OpenSource") == "#GoLang #OpenSource"


def test_reserved_set_contains_expected():
    assert frozenset("|{}@[]()<>#\\*_~") == LITTLE_TEXT_RESERVED
