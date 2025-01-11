import re
import json

from dataclasses import dataclass, field


def contains_chinese(s):
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    return bool(chinese_pattern.search(s))

def contains_japanese(text):
    japanese_pattern = re.compile(
        r'[\u3040-\u309f\u30a0-\u30ff\u3000-\u303f\uff00-\uffef\u4e00-\u9fff]'
    )
    return bool(japanese_pattern.search(text))

def contains_korean(text):
    korean_pattern = re.compile(
        r'[\uAC00-\uD7AF]'  # Hangul Syllables
        r'|[\u1100-\u11FF]'  # Hangul Jamo
        r'|[\u3130-\u318F]'  # Hangul Compatibility Jamo
        r'|[\uA960-\uA97F]'  # Hangul Jamo Extended-A
        r'|[\uD7B0-\uD7FF]'  # Hangul Jamo Extended-B
    )
    return bool(korean_pattern.search(text))

def print_json(json_str: str):
    print(json.dumps(json_str, indent=4, ensure_ascii=False))
    # save to ./test.json
    with open("test.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(json_str, indent=4, ensure_ascii=False))




@dataclass
class AppleSong:
    id: str
    name: str
    artist: str
    album: str

@dataclass
class ApplePlaylist:
    id: str
    name: str
    create_time: str
    songs: list[AppleSong] = field(default_factory=list)