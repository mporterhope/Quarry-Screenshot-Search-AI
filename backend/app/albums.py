from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Album:
    id: str
    name: str
    rule: Dict


class AlbumStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.path = self.data_dir / "albums.jsonl"
        self.albums: List[Album] = []
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        self.albums.clear()
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                self.albums.append(Album(**obj))

    def save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            for album in self.albums:
                f.write(json.dumps(asdict(album), ensure_ascii=False) + "\n")

    def list(self) -> List[Album]:
        return list(self.albums)

    def get(self, album_id: str) -> Optional[Album]:
        for a in self.albums:
            if a.id == album_id:
                return a
        return None

    def create(self, name: str, rule: Dict) -> Album:
        album = Album(id=f"alb_{len(self.albums):06d}", name=name, rule=rule)
        self.albums.append(album)
        self.save()
        return album

    def rename(self, album_id: str, name: str) -> Optional[Album]:
        a = self.get(album_id)
        if not a:
            return None
        a.name = name
        self.save()
        return a

    def delete(self, album_id: str) -> bool:
        before = len(self.albums)
        self.albums = [a for a in self.albums if a.id != album_id]
        if len(self.albums) != before:
            self.save()
            return True
        return False


