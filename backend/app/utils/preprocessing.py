import re
import unicodedata
from typing import Tuple, Optional, Set

YEAR_REGEX = re.compile(r"\s*\((\d{4})\)\s*$")
ARTICLES = {"the", "a", "an", "les", "la", "le", "el", "il", "der", "die", "das", "l'"}

def extract_year_and_clean(raw_title: str) -> Tuple[str, Optional[int]]:
    """
    Extracts trailing year (YYYY) if present.
    Returns (title_without_year, year_int_or_none).
    Optional-match regex guarantees safety for titles without trailing year.
    """
    raw_title = raw_title.strip()
    match = YEAR_REGEX.search(raw_title)
    if match:
        year = int(match.group(1))
        clean_title = raw_title[:match.start()].strip()
        return clean_title, year
    return raw_title, None

def remove_diacritics(text: str) -> str:
    """NFKD normalize and strip combining characters (e.g. misérables -> miserables)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def unfold_article(title_str: str) -> Set[str]:
    """
    Unfolds trailing article if present (e.g. 'Matrix, The' -> 'the matrix', 'matrix').
    """
    results = {title_str.strip()}
    if "," in title_str:
        parts = [p.strip() for p in title_str.split(",")]
        if len(parts) == 2 and parts[1].lower() in ARTICLES:
            article = parts[1].lower()
            main_part = parts[0]
            results.add(f"{article} {main_part}".strip())
            results.add(main_part)
        elif len(parts) > 2:
            # Handle cases like Postman, The (Postino, Il)
            main_part = parts[0]
            results.add(main_part)
    return results

def clean_paren_content(content: str) -> str:
    """Strips markers like 'a.k.a. ', 'aka ', 'original title: '."""
    cleaned = re.sub(r"^(a\.k\.a\.|aka|original title:)\s*", "", content, flags=re.IGNORECASE)
    return cleaned.strip()

def normalize_string_basic(s: str) -> str:
    """Basic normalization: lowercase, diacritics removal, apostrophe normalization, punctuation collapse."""
    s = s.lower()
    s = remove_diacritics(s)
    s = s.replace("’", "'")
    # replace punctuation other than single quotes with space
    s = re.sub(r"[^\w\s']", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def generate_title_aliases(raw_title: str) -> Tuple[Optional[int], str, Set[str]]:
    """
    Parses raw_title from movies.csv and emits:
    (year, clean_title, set_of_searchable_aliases)
    """
    clean_title, year = extract_year_and_clean(raw_title)
    aliases: Set[str] = set()

    # Extract secondary parenthetical groups if present (e.g. Seven (a.k.a. Se7en))
    parens = re.findall(r"\(([^)]+)\)", clean_title)
    base_title = re.sub(r"\([^)]+\)", "", clean_title).strip()

    # Process base title and parens
    titles_to_process = [base_title]
    for p in parens:
        cleaned_p = clean_paren_content(p)
        if cleaned_p:
            titles_to_process.append(cleaned_p)

    for t in titles_to_process:
        # Unfold articles for each candidate title component
        unfolded_variants = unfold_article(t)
        for var in unfolded_variants:
            norm = normalize_string_basic(var)
            if norm:
                aliases.add(norm)
                # Emit de-apostrophe variant if apostrophe exists
                if "'" in norm:
                    aliases.add(norm.replace("'", ""))
                # Emit de-spaced variant
                despaced = norm.replace(" ", "").replace("'", "")
                if len(despaced) > 2:
                    aliases.add(despaced)

    # If year exists, add alias variants with year attached (e.g. "dark knight 2008")
    if year:
        year_str = str(year)
        base_aliases = list(aliases)
        for a in base_aliases:
            aliases.add(f"{a} {year_str}")

    return year, clean_title, aliases
