from pathlib import Path
from app.indexer import ScreenshotIndexer


class DummyIndexer(ScreenshotIndexer):
    def _ocr(self, image):  # type: ignore
        return "Your booking reference is ABC123 and total $42.00"

    def _ocr_with_blocks(self, image):  # type: ignore
        # Minimal block list for highlight semantics
        blocks = [
            {"text": "Your", "conf": 90, "bbox": {"x": 0, "y": 0, "w": 10, "h": 10}},
            {"text": "booking", "conf": 90, "bbox": {"x": 10, "y": 0, "w": 10, "h": 10}},
            {"text": "reference", "conf": 90, "bbox": {"x": 20, "y": 0, "w": 10, "h": 10}},
            {"text": "ABC123", "conf": 90, "bbox": {"x": 30, "y": 0, "w": 10, "h": 10}},
        ]
        return ("Your booking reference is ABC123 and total $42.00", blocks)

    def _embed(self, text: str):  # type: ignore
        # Deterministic small vector of correct dim
        import numpy as np
        v = np.zeros(self.dim, dtype="float32")
        v[0] = 1.0
        return v.tolist()


def test_index_and_search(tmp_path: Path):
    idx = DummyIndexer(data_dir=tmp_path)
    # Create a tiny blank image
    from PIL import Image
    import io
    buf = io.BytesIO()
    Image.new('RGB', (50, 20), color='white').save(buf, format='PNG')
    content = buf.getvalue()

    meta = idx.index_image_bytes(content, filename='a.png')
    assert meta['id'] == '00000000'
    assert 'entities' in meta and 'amount' in meta['entities'] and 'code' in meta['entities']

    res = idx.search('booking')
    assert len(res) >= 1

    # Date filter outside range should exclude
    res2 = idx.search('booking', start_date='2999-01-01')
    assert res2 == []


