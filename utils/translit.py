from typing import Optional

from transliterate import translit
from transliterate.base import TranslitLanguagePack, registry


class SEOLanguagePack(TranslitLanguagePack):
    """Transliteration rules for generating SEO-friendly slugs from Russian text."""

    language_code = "SEO"
    language_name = "RuSEO"
    mapping = (
        "абвгдезийклмнопрстуфхцы.,/",
        "abvgdezijklmnoprstufhcy---",
    )
    # Letter 'х' → 'kh' after k, z, c, s, e, h; otherwise → 'h'

    pre_processor_mapping = {
        "кх": "kkh",
        "зх": "zkh",
        "цх": "ckh",
        "сх": "skh",
        "ех": "ekh",
        "жх": "zhkh",
        "чх": "chkh",
        "шх": "shkh",
        "щх": "shchkh",
        "эх": "ehkh",
        "ё": "yo",
        "ж": "zh",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "",
        "ь": "",
        "э": "eh",
        "ю": "yu",
        "я": "ya",
        "+": "plyus",
    }


class RuLanguagePack(TranslitLanguagePack):
    """Transliteration rules for converting Latin text back into Cyrillic."""

    language_code = "ru"
    language_name = "Ru"
    mapping = (
        "abvgdezijklmnoprstufhcy",  # Latin alphabet
        "абвгдезийклмнопрстуфхцы",  # Cyrillic alphabet
    )
    # Letter 'kh' → 'х', 'shch' → 'щ', etc.

    pre_processor_mapping = {
        "yo": "ё",
        "zh": "ж",
        "kh": "х",
        "ck": "к",
        "ch": "ч",
        "sh": "ш",
        "shch": "щ",
        "yu": "ю",
        "ya": "я",
        "eh": "э",
    }


# Register both transliteration packs
registry.register(SEOLanguagePack)
registry.register(RuLanguagePack)


def to_chpu(name: str, last_slug: Optional[str] = None) -> str:
    """
    Generates a unique SEO-friendly slug from a given name.
    If `last_slug` is provided and ends with a number, increments it.
    Otherwise, transliterates the name and replaces spaces with hyphens.
    """
    name = str(name)
    if last_slug:
        if "-" in last_slug and last_slug.split("-")[-1].isdigit():
            parts = last_slug.split("-")
            parts[-1] = str(int(parts[-1]) + 1)
            chpu = "-".join(parts)
        else:
            chpu = f"{last_slug}-1"
    else:
        chpu = name.lower()
        chpu = translit(chpu, "SEO")
        chpu = "".join(x for x in chpu if x.isalnum() or x in {" ", "-"})
        if " " in chpu:
            chpu = "-".join(filter(None, chpu.split(" ")))
    return chpu


def to_latin(text: str) -> str:
    """Transliterates a Russian string into Latin characters."""
    return translit(str(text).lower(), "SEO")


def to_cyrillic(text: str) -> str:
    """Transliterates a Latin string back into Cyrillic characters."""
    return translit(str(text).lower(), "ru")
