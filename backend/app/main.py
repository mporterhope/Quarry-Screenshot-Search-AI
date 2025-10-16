from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn

from .indexer import ScreenshotIndexer
from .albums import AlbumStore
from starlette.staticfiles import StaticFiles


app = FastAPI(title="Quarry.io API", version="0.1.0")

# Allow local dev frontends by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

indexer = ScreenshotIndexer()
albums = AlbumStore(indexer.data_dir)

# Serve stored images (e.g., /images/00000001.jpg)
app.mount("/images", StaticFiles(directory=str(indexer.images_dir)), name="images")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/index")
async def index_images(
    files: List[UploadFile] = File(...),
    collection: Optional[str] = Form(None),
):
    try:
        results = []
        for f in files:
            content = await f.read()
            meta = indexer.index_image_bytes(content, filename=f.filename, collection=collection)
            results.append(meta)
        indexer.save()
        return {"indexed": results}
    except Exception as e:  # pragma: no cover (logged to response)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/search")
def search_images(
    q: str,
    k: int = 12,
    collection: Optional[str] = None,
    entity_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    album_id: Optional[str] = None,
    type_label: Optional[str] = None,
):
    try:
        # If album_id present, merge its rule into parameters
        if album_id:
            album = albums.get(album_id)
            if not album:
                return JSONResponse(status_code=404, content={"error": "album not found"})
            rule = album.rule or {}
            q_rule = rule.get("q")
            if q_rule and not q:
                q = q_rule
            collection = rule.get("collection", collection)
            entity_type = rule.get("entity_type", entity_type)
            start_date = rule.get("start_date", start_date)
            end_date = rule.get("end_date", end_date)

        matches = indexer.search(
            q,
            k=k,
            collection=collection,
            entity_type=entity_type,
            start_date=start_date,
            end_date=end_date,
            type_label=type_label,
        )
        return {"query": q, "results": matches}
    except Exception as e:  # pragma: no cover
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/image/{image_id}/ocr")
def get_image_ocr(image_id: str):
    try:
        ocr_path = indexer.ocr_dir / f"{image_id}.json"
        if not ocr_path.exists():
            return JSONResponse(status_code=404, content={"error": "ocr not found"})
        import json, re
        with ocr_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Map entities to blocks by substring match (best-effort)
        meta = indexer.get_meta(image_id)
        entity_to_block_idxs = {}
        if meta and meta.entities:
            blocks = data.get("blocks", [])
            for etype, values in meta.entities.items():
                hits = []
                for v in values:
                    v_low = v.strip().lower()
                    for i, b in enumerate(blocks):
                        if v_low and v_low in str(b.get("text", "")).lower():
                            hits.append(i)
                if hits:
                    entity_to_block_idxs[etype] = sorted(list(set(hits)))
        data["entity_block_idxs"] = entity_to_block_idxs
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/albums")
def list_albums():
    return {"albums": [
        {"id": a.id, "name": a.name, "rule": a.rule} for a in albums.list()
    ]}


@app.post("/albums")
def create_album(name: str = Form(...), rule: str = Form(...)):
    try:
        import json
        rule_obj = json.loads(rule)
        a = albums.create(name=name, rule=rule_obj)
        return {"album": {"id": a.id, "name": a.name, "rule": a.rule}}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.post("/albums/{album_id}/rename")
def rename_album(album_id: str, name: str = Form(...)):
    a = albums.rename(album_id, name)
    if not a:
        return JSONResponse(status_code=404, content={"error": "album not found"})
    return {"album": {"id": a.id, "name": a.name, "rule": a.rule}}


@app.delete("/albums/{album_id}")
def delete_album(album_id: str):
    ok = albums.delete(album_id)
    if not ok:
        return JSONResponse(status_code=404, content={"error": "album not found"})
    return {"deleted": True}


@app.get("/export.json")
def export_json():
    # Light-weight export of meta + entities (texts stored inside meta.text)
    return {
        "images": [
            {
                "id": m.id,
                "filename": m.filename,
                "text": m.text,
                "width": m.width,
                "height": m.height,
                "collection": m.collection,
                "imported_at": m.imported_at,
                "entities": m.entities,
                "image_path": f"images/{m.id}.jpg",
            }
            for m in indexer.metas
        ]
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


