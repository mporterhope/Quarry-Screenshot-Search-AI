from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss  # type: ignore
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer
from datetime import datetime, timezone


DEFAULT_DATA_DIR = Path(os.environ.get("QUARRY_DATA_DIR", "./data")).resolve()
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ImageMeta:
    id: str
    filename: str
    text: str
    width: int
    height: int
    collection: Optional[str] = None
    imported_at: str = ""  # ISO 8601
    type_label: Optional[str] = None
    entities: Optional[Dict[str, List[str]]] = None


class ScreenshotIndexer:
    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.data_dir = data_dir
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

        self.index_path = self.data_dir / "index.faiss"
        self.meta_path = self.data_dir / "meta.jsonl"
        self.images_dir = self.data_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.ocr_dir = self.data_dir / "ocr"
        self.ocr_dir.mkdir(parents=True, exist_ok=True)

        self.id_to_offset: Dict[str, int] = {}
        self.metas: List[ImageMeta] = []

        if self.index_path.exists() and self.meta_path.exists():
            self._load()
        else:
            self.index = faiss.IndexFlatIP(self.dim)

    # ---------- persistence ----------
    def _load(self) -> None:
        self.index = faiss.read_index(str(self.index_path))
        with self.meta_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                meta = ImageMeta(**json.loads(line))
                self.metas.append(meta)
                self.id_to_offset[meta.id] = i

    def save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        with self.meta_path.open("w", encoding="utf-8") as f:
            for meta in self.metas:
                f.write(json.dumps(asdict(meta), ensure_ascii=False) + "\n")

    # ---------- core ops ----------
    def _ocr(self, image: Image.Image) -> str:
        # Simple OCR using Tesseract; users may configure TESSDATA_PREFIX externally
        text = pytesseract.image_to_string(image)
        return text.strip()

    def _embed(self, text: str) -> List[float]:
        emb = self.model.encode([text], normalize_embeddings=True)[0]
        return emb.astype("float32").tolist()  # type: ignore

    def index_image_bytes(self, content: bytes, filename: str, collection: Optional[str] = None) -> Dict:
        image = Image.open(io.BytesIO(content)).convert("RGB")
        text, ocr_blocks = self._ocr_with_blocks(image)
        vector = self._embed(text)
        entities = self._extract_entities(text)
        type_label = self._classify_type(text)

        img_id = f"{len(self.metas):08d}"
        meta = ImageMeta(
            id=img_id,
            filename=filename,
            text=text,
            width=image.width,
            height=image.height,
            collection=collection,
            imported_at=datetime.now(timezone.utc).isoformat(),
            type_label=type_label,
            entities=entities,
        )

        # Persist original image for previews
        out_path = self.images_dir / f"{img_id}.jpg"
        image.save(out_path, format="JPEG", quality=85)

        # Persist OCR blocks per image
        with (self.ocr_dir / f"{img_id}.json").open("w", encoding="utf-8") as f:
            import json as _json
            _json.dump({"blocks": ocr_blocks}, f, ensure_ascii=False)

        import numpy as np  # local import to avoid global dependency at import time

        vec_np = np.array([vector], dtype="float32")
        if not self.index.is_trained:
            # For IndexFlatIP, training isn't needed, but keep branch for future swap
            pass
        self.index.add(vec_np)

        self.metas.append(meta)
        self.id_to_offset[meta.id] = len(self.metas) - 1

        return {
            "id": meta.id,
            "filename": meta.filename,
            "text": meta.text,
            "width": meta.width,
            "height": meta.height,
            "collection": meta.collection,
            "imported_at": meta.imported_at,
            "type_label": meta.type_label,
            "entities": meta.entities,
            "image_path": str(out_path.relative_to(self.data_dir)),
        }

    def search(self, query: str, k: int = 12, collection: Optional[str] = None, entity_type: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, type_label: Optional[str] = None) -> List[Dict]:
        if len(self.metas) == 0:
            return []

        import numpy as np

        q_vec = self.model.encode([query], normalize_embeddings=True).astype("float32")
        scores, idxs = self.index.search(q_vec, min(k, len(self.metas)))

        results: List[Tuple[int, float]] = []
        for i, score in zip(idxs[0].tolist(), scores[0].tolist()):
            if i < 0:
                continue
            meta = self.metas[i]
            if collection is not None and meta.collection != collection:
                continue
            if entity_type is not None:
                if not meta.entities or entity_type not in meta.entities or len(meta.entities[entity_type]) == 0:
                    continue
            if start_date or end_date:
                try:
                    ts = datetime.fromisoformat(meta.imported_at.replace("Z", "+00:00")).date()
                    if start_date:
                        sd = datetime.fromisoformat(start_date).date()
                        if ts < sd:
                            continue
                    if end_date:
                        ed = datetime.fromisoformat(end_date).date()
                        if ts > ed:
                            continue
                except Exception:
                    pass
            if type_label is not None and meta.type_label != type_label:
                continue
            results.append((i, float(score)))

        # Map to payloads
        out: List[Dict] = []
        for i, score in results:
            meta = self.metas[i]
            out.append(
                {
                    "id": meta.id,
                    "filename": meta.filename,
                    "text": meta.text,
                    "width": meta.width,
                    "height": meta.height,
                    "collection": meta.collection,
                    "imported_at": meta.imported_at,
                    "type_label": meta.type_label,
                    "score": score,
                    "entities": meta.entities,
                    "image_path": f"images/{meta.id}.jpg",
                }
            )
        return out

    # ---------- OCR with blocks ----------
    def _ocr_with_blocks(self, image: Image.Image):
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        blocks = []
        texts: List[str] = []
        n = len(data.get("text", []))
        for i in range(n):
            text = data["text"][i] or ""
            if text.strip() == "":
                continue
            conf_raw = data.get("conf", ["0"]) [i] if isinstance(data.get("conf"), list) else "0"
            try:
                conf = float(conf_raw)
            except Exception:
                conf = -1.0
            left = int(data["left"][i])
            top = int(data["top"][i])
            width = int(data["width"][i])
            height = int(data["height"][i])
            blocks.append({
                "text": text,
                "conf": conf,
                "bbox": {"x": left, "y": top, "w": width, "h": height},
            })
            texts.append(text)
        return (" ".join(texts).strip(), blocks)

    # ---------- type classification (heuristic) ----------
    def _classify_type(self, text: str) -> Optional[str]:
        t = text.lower()
        rules = [
            ("receipt", ["total", "subtotal", "visa", "mastercard", "amount due", "invoice"]),
            ("booking", ["booking", "pnr", "reservation", "itinerary", "check-in", "flight"]),
            ("chat", ["sent", "delivered", "pm", ":", "am", "today", "yesterday"]),
            ("code", ["error", "exception", "function", "class", " var ", " const ", " def "]),
            ("slide", ["slide", "presentation", "agenda"]),
            ("whiteboard", ["whiteboard", "marker", "sketch"]),
            ("article", ["read more", "subscribe", "by ", "comments"]),
            ("map", ["directions", "km", "mi", "route"]),
        ]
        for label, keywords in rules:
            hits = sum(1 for kw in keywords if kw in t)
            if hits >= 2:
                return label
        return None

    # ---------- meta lookup ----------
    def get_meta(self, image_id: str) -> Optional[ImageMeta]:
        idx = self.id_to_offset.get(image_id)
        if idx is None:
            return None
        if 0 <= idx < len(self.metas):
            return self.metas[idx]
        return None

    # ---------- entities ----------
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        import re
        entities: Dict[str, List[str]] = {
            "url": [],
            "email": [],
            "phone": [],
            "date": [],
            "amount": [],
            "code": [],
        }

        url_re = re.compile(r"https?://[\w\-._~:/?#\[\]@!$&'()*+,;=%]+", re.I)
        entities["url"] = list({m.group(0) for m in url_re.finditer(text)})

        email_re = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
        entities["email"] = list({m.group(0) for m in email_re.finditer(text)})

        phone_re = re.compile(r"(?:(?:\+\d{1,3}[ \-]?)?(?:\(?\d{3}\)?[ \-]?)?\d{3}[ \-]?\d{4})")
        entities["phone"] = list({m.group(0) for m in phone_re.finditer(text)})

        date_re = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})\b")
        entities["date"] = list({m.group(0) for m in date_re.finditer(text)})

        amount_re = re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?")
        entities["amount"] = list({m.group(0) for m in amount_re.finditer(text)})

        code_re = re.compile(r"\b[A-Z0-9]{5,8}\b")
        entities["code"] = list({m.group(0) for m in code_re.finditer(text)})

        return {k: v for k, v in entities.items() if v}


