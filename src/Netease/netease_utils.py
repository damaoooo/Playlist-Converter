import json
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

def print_json(json_str: str):
    print(json.dumps(json_str, indent=4, ensure_ascii=False))
    # save to ./test.json
    with open("test.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(json_str, indent=4, ensure_ascii=False))

@dataclass
class NeteaseSong:
    id: int
    name: str
    artists: list[str]
    album: str

@dataclass
class NeteasePlaylist:
    name: str
    id: int
    creator_id: int
    create_time: int
    songs: List[NeteaseSong] = field(default_factory=list)

    def print_playlist(self):
        create_time_human_readable = datetime.fromtimestamp(self.create_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f"ID: {self.id}, Name: {self.name}, Create Time: {create_time_human_readable}")
