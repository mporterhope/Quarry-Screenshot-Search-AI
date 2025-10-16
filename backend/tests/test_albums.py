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


def test_album_id_collision_regression(tmp_path: Path):
    """Test that deleting and recreating albums doesn't cause ID collisions"""
    store = AlbumStore(tmp_path)
    
    # Create first album
    a1 = store.create(name="First", rule={"q": "test1"})
    original_id = a1.id
    assert store.get(original_id) is not None
    
    # Delete it
    store.delete(original_id)
    assert store.get(original_id) is None
    
    # Create second album - should get different ID
    a2 = store.create(name="Second", rule={"q": "test2"})
    new_id = a2.id
    assert new_id != original_id
    assert store.get(new_id) is not None
    assert store.get(original_id) is None  # Original still gone
    
    # Create third album - should get another different ID
    a3 = store.create(name="Third", rule={"q": "test3"})
    third_id = a3.id
    assert third_id != original_id
    assert third_id != new_id
    assert len({original_id, new_id, third_id}) == 3  # All unique


