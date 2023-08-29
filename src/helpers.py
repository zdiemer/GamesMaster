import html
import re
import unicodedata
from typing import List

from excel_game import ExcelGame as ExcelGame
from constants import PLATFORM_NAMES

def titles_equal_normalized(t1: str, t2: str):
    if t1 is None or t2 is None:
        return False
    return normalize(t1) == normalize(t2)

def normalize(s: str):
    return ''.join(
        filter(
            str.isalnum,
            unicodedata.normalize(
                'NFKD',
                re.sub(
                    r'( \([0-9]{4}\))', '', html.unescape(s).casefold().replace('&', 'and'))).strip()))

def validate(game: ExcelGame, title: str, platforms: List[str]):
    return titles_equal_normalized(game.title, title) \
        and verify_platform(game.platform, platforms)

def verify_platform(platform: str, platforms: List[str]):
    if platforms is None or not any(platforms):
        return False
    return any(
        filter(
        lambda p: p.lower() == platform.lower() or p.lower() in PLATFORM_NAMES[platform.lower()],
        platforms))