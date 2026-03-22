from __future__ import annotations

import re
import unicodedata
from difflib import get_close_matches


ABBREV_MAP = {
    "tm": "thu muc",
    "dc": "di chuyen",
    "scp": "sao chep",
    "dt": "doi ten",
    "ds": "danh sach",
    "mk": "mo",
    "xf": "xoa file",
    "desk": "desktop",
    "mh": "man hinh",
    "timf": "tim file",
}

PHRASE_REPLACEMENTS = {
    "man hinh desk": "desktop",
    "man hinh desktop": "desktop",
    "o man hinh desk": "desktop",
    "o man hinh desktop": "desktop",
    "o man hinh": "desktop",
    "liueeju": "lieu",
    "du lieu": "du_lieu",
    "du lieuu": "du_lieu",
    "vao do": "vao_do",
    "roi vao": "roi vao",
    "o d:": "o d",
    "o d\\": "o d",
}

VOCAB = [
    "tao",
    "thu",
    "muc",
    "desktop",
    "du",
    "lieu",
    "di",
    "chuyen",
    "vao",
    "backup",
    "o",
    "d",
    "sao",
    "chep",
    "doi",
    "ten",
    "nen",
    "zip",
    "xem",
    "liet",
    "ke",
    "file",
    "doc",
    "ghi",
    "xoa",
    "tim",
    "man",
    "hinh",
    "roi",
    "timf",
    "desktop",
    "du_lieu",
]


def normalize_text(text: str) -> str:
    t = text.strip().lower()
    t = "".join(ch for ch in unicodedata.normalize("NFD", t) if unicodedata.category(ch) != "Mn")
    t = re.sub(r"[^a-z0-9_:\\\s]", " ", t)
    for src, dst in PHRASE_REPLACEMENTS.items():
        t = t.replace(src, dst)
    t = re.sub(r"\s+", " ", t)
    tokens = t.split(" ")
    expanded: list[str] = []
    for tok in tokens:
        if tok in ABBREV_MAP:
            expanded.extend(ABBREV_MAP[tok].split(" "))
        else:
            expanded.append(tok)
    corrected = [_correct_token(tok) for tok in expanded]
    return " ".join(corrected)


def _correct_token(tok: str) -> str:
    if len(tok) < 3:
        return tok
    if tok in VOCAB:
        return tok
    m = get_close_matches(tok, VOCAB, n=1, cutoff=0.82)
    return m[0] if m else tok
