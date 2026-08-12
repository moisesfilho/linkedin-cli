# Official LinkedIn "little text" reserved characters (15):
# \ | { } @ [ ] ( ) < > # * _ ~
# https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/little-text-format
LITTLE_TEXT_RESERVED = frozenset("|{}@[]()<>#\\*_~")


def escape_little_text(text: str) -> str:
    """Escape LinkedIn 'little' text reserved characters in a commentary.

    The Posts API renders the commentary as "little text": unescaped reserved
    characters silently truncate or misparse the post (e.g. everything after
    an unescaped '(' is dropped), so they are backslash-escaped unless they
    form a supported element. The escape backslash is consumed by LinkedIn's
    parser and is NOT rendered in the published post.

    Double quotes are NOT reserved by little text and must not be escaped,
    otherwise the backslash is rendered literally.
    """
    return "".join(_escape_char(text, index, char) for index, char in enumerate(text))


def _escape_char(text: str, index: int, char: str) -> str:
    if char == "#" and _is_hashtag(text, index):
        return char
    if char in LITTLE_TEXT_RESERVED:
        return "\\" + char
    return char


def _is_hashtag(text: str, index: int) -> bool:
    if index + 1 >= len(text) or not text[index + 1].isalnum():
        return False
    return index == 0 or not text[index - 1].isalnum()
