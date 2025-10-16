from pathlib import Path
from typing import Dict, List, Optional
from fastapi.testclient import TestClient


def make_client(tmp_path: Path):
    # Import here to ensure module-level globals are available
    from app import main as app_main

    class FakeIndexer:
        def __init__(self, data_dir: Path):
            self.data_dir = data_dir
            self.images_dir = self.data_dir / "images"
            self.images_dir.mkdir(parents=True, exist_ok=True)
            self.ocr_dir = self.data_dir / "ocr"
            self.ocr_dir.mkdir(parents=True, exist_ok=True)
            self.metas: List[object] = []

        def index_image_bytes(self, content: bytes, filename: str, collection: Optional[str] = None) -> Dict:
            img_id = f"{len(self.metas):08d}"
            meta = type("M", (), {
                "id": img_id,
                "filename": filename,
                "text": "dummy text ABC123 $10",
                "width": 10,
                "height": 10,
                "collection": collection,
                "imported_at": "2025-01-01T00:00:00Z",
                "type_label": "receipt",
                "entities": {"code": ["ABC123"], "amount": ["$10"]},
            })()
            self.metas.append(meta)
            # Write OCR file
            (self.ocr_dir / f"{img_id}.json").write_text('{"blocks":[{"text":"ABC123","conf":90,"bbox":{"x":0,"y":0,"w":5,"h":5}}]}', encoding="utf-8")
            # Persist a fake image
            (self.images_dir / f"{img_id}.jpg").write_bytes(content)
            return {
                "id": img_id,
                "filename": filename,
                "text": meta.text,
                "width": meta.width,
                "height": meta.height,
                "collection": collection,
                "imported_at": meta.imported_at,
                "type_label": meta.type_label,
                "entities": meta.entities,
                "image_path": f"images/{img_id}.jpg",
            }

        def save(self):
            pass

        def search(self, q: str, k: int = 12, collection: Optional[str] = None, entity_type: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, type_label: Optional[str] = None):
            # Return all metas as results with dummy score
            out = []
            for m in self.metas:
                out.append({
                    "id": m.id,
                    "filename": m.filename,
                    "text": m.text,
                    "width": m.width,
                    "height": m.height,
                    "collection": m.collection,
                    "imported_at": m.imported_at,
                    "type_label": m.type_label,
                    "entities": m.entities,
                    "score": 0.9,
                    "image_path": f"images/{m.id}.jpg",
                })
            return out

        def get_meta(self, image_id: str):
            for m in self.metas:
                if m.id == image_id:
                    return m
            return None

    # Patch the global indexer
    app_main.indexer = FakeIndexer(tmp_path)

    return TestClient(app_main.app)


def test_health(tmp_path: Path):
    client = make_client(tmp_path)
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_index_and_search_and_export(tmp_path: Path):
    client = make_client(tmp_path)
    # Upload a tiny file
    files = {"files": ("a.jpg", b"fakejpegbytes", "image/jpeg")}
    r = client.post("/index", files=files)
    assert r.status_code == 200
    rid = r.json()["indexed"][0]["id"]

    r2 = client.get("/search", params={"q": "abc"})
    assert r2.status_code == 200
    assert any(x["id"] == rid for x in r2.json()["results"])

    r3 = client.get("/export.json")
    assert r3.status_code == 200
    assert any(img["id"] == rid for img in r3.json()["images"])


def test_albums_crud_and_use(tmp_path: Path):
    client = make_client(tmp_path)
    # Create album
    r = client.post("/albums", data={"name": "Test", "rule": '{"q":"hello"}'})
    assert r.status_code == 200
    alb = r.json()["album"]
    # List
    r2 = client.get("/albums")
    assert r2.status_code == 200 and any(a["id"] == alb["id"] for a in r2.json()["albums"])
    # Rename
    r3 = client.post(f"/albums/{alb['id']}/rename", data={"name": "Renamed"})
    assert r3.status_code == 200 and r3.json()["album"]["name"] == "Renamed"
    # Delete
    r4 = client.delete(f"/albums/{alb['id']}")
    assert r4.status_code == 200 and r4.json()["deleted"] is True


def test_ocr_endpoint(tmp_path: Path):
    client = make_client(tmp_path)
    files = {"files": ("a.jpg", b"fakejpegbytes", "image/jpeg")}
    r = client.post("/index", files=files)
    rid = r.json()["indexed"][0]["id"]
    r2 = client.get(f"/image/{rid}/ocr")
    assert r2.status_code == 200
    data = r2.json()
    assert "blocks" in data

