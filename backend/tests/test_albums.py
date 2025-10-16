from pathlib import Path
from app.albums import AlbumStore


def test_album_crud(tmp_path: Path):
    store = AlbumStore(tmp_path)
    a = store.create(name="Test", rule={"q": "hello"})
    assert a.id.startswith("alb_")
    assert store.get(a.id) is not None

    a2 = store.rename(a.id, "Renamed")
    assert a2 and a2.name == "Renamed"

    ok = store.delete(a.id)
    assert ok
    assert store.get(a.id) is None


