from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel
from typing import Optional, List
import os, shutil, mimetypes
from datetime import datetime
from pathlib import Path
import basex_db as db
import dotenv

dotenv.load_dotenv()

UPLOADS_PATH = Path(__file__).parent / "data" / "uploads"

app = FastAPI(title="Content Blender Studio", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic models ─────────────────────────────────────────────────────────

class StyleIn(BaseModel):
    width: Optional[str] = None
    padding: Optional[str] = None
    margin: Optional[str] = None
    background: Optional[str] = None
    borderRadius: Optional[str] = None
    fontSize: Optional[str] = None
    fontWeight: Optional[str] = None
    color: Optional[str] = None
    lineHeight: Optional[str] = None
    objectFit: Optional[str] = None
    aspectRatio: Optional[str] = None
    hidden: Optional[str] = None

class PlacementIn(BaseModel):
    refId: str
    order: int
    layout: Optional[str] = "body"
    style: Optional[StyleIn] = None

class BlendIn(BaseModel):
    title: str
    target: str = "Web"
    placements: List[PlacementIn] = []

# ─── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    UPLOADS_PATH.mkdir(parents=True, exist_ok=True)
    db.check_databases()
    print("✓ Content Blender Backend Ready")

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}

@app.get("/api/bank")
def get_bank():
    items = db.get_all_items()
    return {"items": items}

@app.post("/api/bank/text")
async def add_text(
    title: str = Form(...),
    body: str = Form(...),
    author: str = Form("Anonymous")
):
    iid, item = db.add_text_item(title, body, author)
    return {"success": True, "id": iid, "item": item}

@app.post("/api/bank/image-url")
async def add_image_url(
    title: str = Form(...),
    src: str = Form(...),
    alt: str = Form(""),
    caption: str = Form(""),
    author: str = Form("Anonymous")
):
    iid, item = db.add_image_item(title, src, alt, caption, author)
    return {"success": True, "id": iid, "item": item}

@app.post("/api/bank/video-url")
async def add_video_url(
    title: str = Form(...),
    src: str = Form(...),
    caption: str = Form(""),
    author: str = Form("Anonymous")
):
    iid, item = db.add_video_item(title, src, caption, author)
    return {"success": True, "id": iid, "item": item}

@app.post("/api/bank/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    caption: str = Form(""),
    author: str = Form("Anonymous")
):
    ct = file.content_type or ""
    if not (ct.startswith("image/") or ct.startswith("video/")):
        raise HTTPException(status_code=400, detail="Only image/* and video/* files are accepted.")

    prefix = "IMG" if ct.startswith("image/") else "VID"
    iid = db.get_next_id(prefix)
    ext = os.path.splitext(file.filename or "")[1].lower() or mimetypes.guess_extension(ct) or ""
    filename = iid + ext
    filepath = UPLOADS_PATH / filename
    
    with open(str(filepath), "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    src = "/api/uploads/" + filename
    item_id, item = db.add_uploaded_item(title, src, ct, caption, author)
    return {"success": True, "id": item_id, "item": item}

@app.delete("/api/bank/{item_id}")
def delete_item(item_id: str):
    db.delete_item(item_id)
    return {"success": True}

@app.get("/api/uploads/{filename}")
def serve_upload(filename: str):
    fp = UPLOADS_PATH / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(fp))

@app.get("/api/bank/export/xml")
def export_bank_xml():
    xml_data = db.export_bank_xml()
    return Response(
        content=xml_data,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=bank.xml"}
    )

@app.get("/api/blends")
def get_blends():
    blends = db.get_all_blends()
    return {"blends": blends}

@app.get("/api/blends/{blend_id}")
def get_blend(blend_id: str):
    blend = db.get_blend(blend_id)
    if blend is None:
        raise HTTPException(status_code=404, detail="Blend not found")
    return blend

@app.post("/api/blends")
def create_blend(data: BlendIn):
    if data.target not in ("Web", "PDF"):
        raise HTTPException(status_code=400, detail="Target must be 'Web' or 'PDF'")
    placements = [p.model_dump() for p in data.placements]
    bid, blend = db.create_blend(data.title, data.target, placements)
    return {"success": True, "id": bid, "blend": blend}

@app.put("/api/blends/{blend_id}")
def update_blend(blend_id: str, data: BlendIn):
    if data.target not in ("Web", "PDF"):
        raise HTTPException(status_code=400, detail="Target must be 'Web' or 'PDF'")
    placements = [p.model_dump() for p in data.placements]
    blend = db.update_blend(blend_id, data.title, data.target, placements)
    return {"success": True, "blend": blend}

@app.delete("/api/blends/{blend_id}")
def delete_blend(blend_id: str):
    db.delete_blend(blend_id)
    return {"success": True}

@app.get("/api/blends/{blend_id}/export/html")
def export_blend_html(blend_id: str):
    blend = db.get_blend_with_items(blend_id)
    if not blend:
        raise HTTPException(status_code=404, detail="Blend not found")

    css_map = {
        "width": "width",
        "padding": "padding",
        "margin": "margin",
        "background": "background",
        "borderRadius": "border-radius",
        "fontSize": "font-size",
        "fontWeight": "font-weight",
        "color": "color",
        "lineHeight": "line-height",
        "objectFit": "object-fit",
        "aspectRatio": "aspect-ratio"
    }

    blocks_html = ""
    for pl in blend["placements"]:
        if pl["style"].get("hidden") == "true":
            continue
        if "item" not in pl:
            continue
        item = pl["item"]
        st = pl["style"]
        mt = item["mediaType"]
        layout = pl["layout"]

        if mt == "text/plain":
            if layout == "hero":
                bg = st.get("background") or "#1a1a2e"
                pad = st.get("padding") or "48px 40px"
                fs = st.get("fontSize") or "32px"
                fw = st.get("fontWeight") or "800"
                col = st.get("color") or "#ffffff"
                w = st.get("width") or "100%"
                extra = ""
                if st.get("margin"):
                    extra += "margin:" + st["margin"] + ";"
                if st.get("borderRadius"):
                    extra += "border-radius:" + st["borderRadius"] + ";"
                blocks_html += (
                    '<section style="background:' + bg + ';padding:' + pad + ';width:' + w + ';box-sizing:border-box;' + extra + '">'
                    '<h1 style="font-family:sans-serif;font-size:' + fs + ';font-weight:' + fw + ';color:' + col + ';margin:0 0 12px 0;">' + item["title"] + '</h1>'
                    '<p style="color:' + col + ';opacity:.85;margin:0 0 8px 0;font-size:16px;">' + (item["body"] or "") + '</p>'
                    '<div style="color:' + col + ';opacity:.4;font-size:12px;">' + (item["meta"].get("author") or "") + ' &bull; ' + (item["meta"].get("created") or "") + '</div>'
                    '</section>'
                )
            else:
                bg = st.get("background") or "#ffffff"
                pad = st.get("padding") or "24px 32px"
                extra = ""
                if st.get("margin"):
                    extra += "margin:" + st["margin"] + ";"
                if st.get("borderRadius"):
                    extra += "border-radius:" + st["borderRadius"] + ";"
                if st.get("width"):
                    extra += "width:" + st["width"] + ";"
                fs = st.get("fontSize") or "20px"
                fw = st.get("fontWeight") or "700"
                col = st.get("color") or "#0e0e16"
                lh = st.get("lineHeight") or "1.6"
                blocks_html += (
                    '<article style="background:' + bg + ';padding:' + pad + ';box-sizing:border-box;' + extra + '">'
                    '<h2 style="border-left:3px solid #7c5cfc;padding-left:12px;font-family:sans-serif;font-size:' + fs + ';font-weight:' + fw + ';color:' + col + ';margin:0 0 12px 0;">' + item["title"] + '</h2>'
                    '<p style="color:' + col + ';line-height:' + lh + ';margin:0;">' + (item["body"] or "") + '</p>'
                    '</article>'
                )
        elif mt.startswith("image/"):
            src = (item["asset"] or {}).get("src", "")
            alt = (item["asset"] or {}).get("alt", item["title"])
            cap = item.get("caption", "")
            ar = st.get("aspectRatio") or "16/9"
            of = st.get("objectFit") or "cover"
            br = st.get("borderRadius") or "0px"
            extra = ""
            if st.get("width"):
                extra += "width:" + st["width"] + ";"
            if st.get("margin"):
                extra += "margin:" + st["margin"] + ";"
            blocks_html += (
                '<figure style="margin:0;padding:0;' + extra + '">'
                '<img src="' + src + '" alt="' + alt + '" style="width:100%;aspect-ratio:' + ar + ';object-fit:' + of + ';border-radius:' + br + ';display:block;" />'
                + ('<figcaption style="padding:8px 12px;font-size:13px;color:#666;">' + cap + '</figcaption>' if cap else '') +
                '</figure>'
            )
        elif mt.startswith("video/"):
            src = (item["asset"] or {}).get("src", "")
            cap = item.get("caption", "")
            ar = st.get("aspectRatio") or "16/9"
            br = st.get("borderRadius") or "0px"
            extra = ""
            if st.get("width"):
                extra += "width:" + st["width"] + ";"
            if st.get("margin"):
                extra += "margin:" + st["margin"] + ";"
            blocks_html += (
                '<figure style="margin:0;padding:0;background:#000;border-radius:' + br + ';overflow:hidden;' + extra + '">'
                '<iframe src="' + src + '" style="width:100%;aspect-ratio:' + ar + ';border:none;display:block;" allowfullscreen></iframe>'
                + ('<figcaption style="padding:8px 12px;font-size:13px;color:#ccc;">' + cap + '</figcaption>' if cap else '') +
                '</figure>'
            )

    html = (
        '<!DOCTYPE html>'
        '<html lang="en">'
        '<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + blend["title"] + '</title>'
        '<style>*{box-sizing:border-box}body{margin:0;font-family:sans-serif;background:#f5f5f5}article,section,figure{display:block}</style>'
        '</head>'
        '<body>' + blocks_html + '</body></html>'
    )
    return HTMLResponse(content=html)

@app.get("/api/blends/{blend_id}/export/xml")
def export_blend_xml(blend_id: str):
    xml_data = db.export_blend_xml(blend_id)
    if not xml_data:
        raise HTTPException(status_code=404, detail="Blend not found")
    return Response(
        content=xml_data,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={blend_id}-export.xml"}
    )
