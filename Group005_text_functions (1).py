"""Bounded narrative helpers required by the FIT5196 A1 public contract.

The functions operate only on values already obtained by a JSON/XML parser.  They
deliberately perform no file I/O and keep the six published single-argument
interfaces unchanged so the pipeline and the teaching-team tests can import them.
"""

import html
import re
import unicodedata


MISSING = "NaN"

# Restrict case-insensitive matching to the published ASCII contract.
ASCII_I = re.IGNORECASE | re.ASCII

# Use ASCII digits and custom boundaries to reject embedded Unicode near-matches.
_ORDER_RE = re.compile(r"(?:HORD|CORD)[0-9]{6}", ASCII_I)
_SKU_RE = re.compile(r"SKU-[A-Za-z0-9]+", ASCII_I)
_PROMO_RE = re.compile(r"B[1-5]SAVE-[0-9]{2}", ASCII_I)


# Unicode Script=Latin letters whose character name does not begin with "LATIN ".
# The name test alone is not the script property: it misses these 229 code points
# (U+00AA FEMININE ORDINAL INDICATOR and U+00BA MASCULINE ORDINAL INDICATOR are
# Latin script, as are the modifier letters and the fullwidth forms), and it wrongly
# accepts GLAGOLITIC ... LATINATE MYSLITE, whose name merely contains "LATIN".
# Verified against Unicode Scripts.txt: zero disagreements over every code point.
_LATIN_SCRIPT_LETTER_RANGES = (
    (0x00AA, 0x00AA), (0x00BA, 0x00BA), (0x02B0, 0x02B8), (0x02E0, 0x02E4),
    (0x1D2C, 0x1D5C), (0x1D9B, 0x1DBE), (0x2071, 0x2071), (0x207F, 0x207F),
    (0x212A, 0x212B), (0x2132, 0x2132), (0x214E, 0x214E), (0x2183, 0x2183),
    (0x2C7D, 0x2C7D), (0xA770, 0xA770), (0xA7F2, 0xA7F4), (0xA7F8, 0xA7F9),
    (0xAB5C, 0xAB5F), (0xAB69, 0xAB69), (0xFF21, 0xFF3A), (0xFF41, 0xFF5A),
    (0x10780, 0x10785), (0x10787, 0x107B0), (0x107B2, 0x107BA),
)


def _is_latin_letter(char):
    """True when char is a letter whose Unicode Script is Latin."""
    if not unicodedata.category(char).startswith("L"):
        return False
    if unicodedata.name(char, "").startswith("LATIN "):
        return True
    code_point = ord(char)
    return any(low <= code_point <= high for low, high in _LATIN_SCRIPT_LETTER_RANGES)


def _is_boundary(char):
    """True when a character may sit next to a reference without embedding it."""
    if char in "_-":
        return False
    return not unicodedata.category(char)[0] in "LNM"


def _search_bounded(pattern, text):
    """First match of pattern that is not embedded in a surrounding word."""
    for match in pattern.finditer(text):
        start, end = match.span()
        before_ok = start == 0 or _is_boundary(text[start - 1])
        after_ok = end == len(text) or _is_boundary(text[end])
        if before_ok and after_ok:
            return match
    return None

# A quoted attribute value may legitimately contain ">" (title="a > b"). Consuming
# up to the first ">" truncates the tag and leaves the remainder as visible residue,
# so quoted runs are matched as single units.
_TAG_RE = re.compile(r"""</?[A-Za-z](?:[^<>"']|"[^"]*"|'[^']*')*>""")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", ASCII_I)
_BRACKETED_MARKER_RE = re.compile(
    r"\[(?:SYSTEM|CATALOGUE|VERIFIED_PURCHASE|SOURCE\s*:[^\]]*|RATING\s*:\s*\d+\s*/\s*5)\]", ASCII_I,
)
_SOCIAL_MARKER_RE = re.compile(r"#verified-buyer|@store_support", ASCII_I)
# Preserve malformed, incomplete or text-separated reference/SKU wrappers.
_REFERENCE_LABEL_RE = re.compile(r"Reference\s*:\s*(?:HORD|CORD)[0-9]{6}", ASCII_I)
_SKU_LABEL_RE = re.compile(r"SKU\s*:\s*SKU-[A-Za-z0-9]+", ASCII_I)
_PROMO_WRAPPER_RE = re.compile(r"PROMO\s*:\s*B[1-5]SAVE-[0-9]{2}", ASCII_I)


def _bounded_spans(pattern, text):
    """Spans of pattern that are not embedded in a surrounding word."""
    spans = []
    for match in pattern.finditer(text):
        start, end = match.span()
        if (start == 0 or _is_boundary(text[start - 1])) and \
           (end == len(text) or _is_boundary(text[end])):
            spans.append((start, end))
    return spans


def _is_separator(gap):
    """Return True when a wrapper gap contains punctuation or whitespace only."""
    return all(unicodedata.category(char)[0] not in "LNM" for char in gap)


def _remove_spans(text, spans, replacement=" "):
    pieces, last = [], 0
    for start, end in sorted(spans):
        if start < last:
            continue
        pieces.append(text[last:start]); pieces.append(replacement); last = end
    pieces.append(text[last:])
    return "".join(pieces)


def _remove_reference_wrapper(text):
    """Remove only a complete Reference/SKU wrapper, separator included."""
    labels = _bounded_spans(_REFERENCE_LABEL_RE, text)
    skus = _bounded_spans(_SKU_LABEL_RE, text)
    spans = []
    for label_start, label_end in labels:
        for sku_start, sku_end in skus:
            if sku_start >= label_end and _is_separator(text[label_end:sku_start]):
                spans.append((label_start, sku_end))
                break
    return _remove_spans(text, spans)


def _remove_promo_wrapper(text):
    return _remove_spans(text, _bounded_spans(_PROMO_WRAPPER_RE, text))


_WHITESPACE_RE = re.compile(r"\s+")

def _is_missing(value):
    """Recognise the published sentinel plus ordinary in-memory absence values."""
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN without a numpy dependency
        return True
    return isinstance(value, str) and (not value.strip() or value.strip() == MISSING)


# Match emoji blocks only, preserving ordinary symbols such as (c), (TM) and degrees.
_EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0x231A, 0x231B),
    (0x23E9, 0x23FA),
    (0x25FD, 0x25FE),
    (0xFE00, 0xFE0F),
    (0x200D, 0x200D),
)


# Remove keycap emoji as complete sequences, including their base character.
_KEYCAP_SEQUENCE_RE = re.compile(r"[0-9#*]\ufe0f?\u20e3")
# Remove a character together with its emoji variation selector.
_EMOJI_VARIATION_RE = re.compile(r".\ufe0f", re.S)


def _is_emoji_character(char):
    """Return True for emoji code points, but not for ordinary text symbols."""
    code = ord(char)
    return any(low <= code <= high for low, high in _EMOJI_RANGES)


def _collapse(value):
    return _WHITESPACE_RE.sub(" ", value).strip()


def clean_narrative_text(value):
    """Accept None or a string; return cleaned multilingual text or ``'NaN'``."""
    if _is_missing(value):
        return MISSING

    text = unicodedata.normalize("NFC", html.unescape(str(value)))
    # Convert Unicode whitespace, including XML non-breaking spaces, to plain spaces.
    text = "".join(" " if (char.isspace() or unicodedata.category(char) == "Zs") else char
                   for char in text)
    text = _TAG_RE.sub(" ", text)
    text = _BRACKETED_MARKER_RE.sub(" ", text)
    text = _remove_spans(text, _bounded_spans(_SOCIAL_MARKER_RE, text))
    text = _URL_RE.sub(" ", text)
    # Remove emoji before matching reference and promotion wrappers.
    text = _KEYCAP_SEQUENCE_RE.sub(" ", text)
    text = _EMOJI_VARIATION_RE.sub(" ", text)
    text = "".join(" " if _is_emoji_character(char) else char for char in text)
    text = _remove_reference_wrapper(text)
    text = _remove_promo_wrapper(text)
    text = _collapse(text).lower()
    return text if text else MISSING


def extract_order_reference(value):
    """Accept None or a string; return an upper-case order reference or ``'NaN'``."""
    if _is_missing(value):
        return MISSING
    match = _search_bounded(_ORDER_RE, str(value))
    return match.group(0).upper() if match else MISSING


def extract_product_sku(value):
    """Accept None or a string; return an upper-case product SKU or ``'NaN'``."""
    if _is_missing(value):
        return MISSING
    match = _search_bounded(_SKU_RE, str(value))
    return match.group(0).upper() if match else MISSING


def extract_promo_code(value):
    """Accept None or a string; return an upper-case promotion code or ``'NaN'``."""
    if _is_missing(value):
        return MISSING
    match = _search_bounded(_PROMO_RE, str(value))
    return match.group(0).upper() if match else MISSING


def build_latin_analysis(value):
    """Accept cleaned multilingual text; return its Latin analysis or ``'NaN'``."""
    if _is_missing(value):
        return MISSING

    text = unicodedata.normalize("NFC", str(value))
    kept = []
    latin_letter_seen = False
    mark_belongs_to_latin = False
    for char in text:
        category = unicodedata.category(char)
        if category.startswith("L"):
            # Keep Latin letters and remove letters from other scripts.
            if _is_latin_letter(char):
                kept.append(char)
                latin_letter_seen = True
                mark_belongs_to_latin = True
            else:
                kept.append(" ")
                mark_belongs_to_latin = False
        elif category.startswith("M"):
            # Keep combining marks only after a retained Latin letter.
            kept.append(char if mark_belongs_to_latin else " ")
        elif category.startswith("N"):
            # Preserve Unicode numeric characters.
            kept.append(char)
            mark_belongs_to_latin = False
        elif char.isspace():
            kept.append(" ")
            mark_belongs_to_latin = False
        elif category.startswith("P"):
            # Remove wide/fullwidth punctuation and preserve other punctuation.
            if unicodedata.east_asian_width(char) in ("W", "F"):
                kept.append(" ")
            else:
                kept.append(char)
            mark_belongs_to_latin = False
        else:
            # Remove emoji and other symbols from the Latin analysis.
            kept.append(" ")
            mark_belongs_to_latin = False

    result = _collapse("".join(kept))
    return result if latin_letter_seen and result else MISSING


def contains_non_latin_script(value):
    """Accept cleaned multilingual text; return a Python bool."""
    if _is_missing(value):
        return False
    return any(
        unicodedata.category(char).startswith("L")
        and not _is_latin_letter(char)
        for char in unicodedata.normalize("NFC", str(value))
    )
