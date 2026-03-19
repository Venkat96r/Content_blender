from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import xml.etree.ElementTree as ET
import os, shutil, mimetypes
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent / "data"
BANK_PATH = BASE / "bank.xml"
BLENDS_PATH = BASE / "blends.xml"
UPLOADS_PATH = BASE / "uploads"

app = FastAPI(title="Content Blender Studio", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── XML helpers ────────────────────────────────────────────────────────────

def load_xml(path: Path, root_tag: str) -> ET.Element:
    if not path.exists():
        root = ET.Element(root_tag)
        save_xml(root, path)
        return root
    try:
        tree = ET.parse(str(path))
        return tree.getroot()
    except ET.ParseError:
        root = ET.Element(root_tag)
        save_xml(root, path)
        return root

def save_xml(root: ET.Element, path: Path):
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write(str(path), encoding="utf-8", xml_declaration=True)

def item_to_dict(el: ET.Element) -> dict:
    title_el = el.find("Title")
    body_el = el.find("Body")
    caption_el = el.find("Caption")
    asset_el = el.find("Asset")
    fallback_el = el.find("Fallback")
    meta_el = el.find("Meta")

    asset = None
    if asset_el is not None:
        asset = {"src": asset_el.get("src", ""), "alt": asset_el.get("alt", "")}

    fallback = None
    if fallback_el is not None:
        thumb_el = fallback_el.find("Thumbnail")
        qr_el = fallback_el.find("QRCode")
        vid_el = fallback_el.find("VideoURL")
        fallback = {
            "thumbnail": thumb_el.get("src", "") if thumb_el is not None else "",
            "qrSrc": qr_el.get("src", "") if qr_el is not None else "",
            "videoURL": vid_el.text if vid_el is not None else ""
        }

    meta = {}
    if meta_el is not None:
        meta = {
            "author": meta_el.get("author", ""),
            "language": meta_el.get("language", "en"),
            "created": meta_el.get("created", "")
        }

    return {
        "id": el.get("ID", ""),
        "mediaType": el.get("MediaType", ""),
        "title": title_el.text if title_el is not None else "",
        "body": body_el.text if body_el is not None else "",
        "caption": caption_el.text if caption_el is not None else "",
        "asset": asset,
        "fallback": fallback,
        "meta": meta
    }

def placement_to_dict(p: ET.Element) -> dict:
    style_el = p.find("Style")
    style = dict(style_el.attrib) if style_el is not None else {}
    return {
        "order": int(p.get("Order", 0)),
        "refId": p.get("RefID", ""),
        "layout": p.get("Layout", "body"),
        "style": style
    }

def blend_to_dict(b: ET.Element) -> dict:
    pls = [placement_to_dict(p) for p in b.findall("Placement")]
    pls.sort(key=lambda x: x["order"])
    return {
        "id": b.get("BlendID", ""),
        "title": b.get("Title", ""),
        "target": b.get("Target", "Web"),
        "createdAt": b.get("CreatedAt", ""),
        "placements": pls
    }

def write_placements(blend_el: ET.Element, placements: list):
    for p_data in sorted(placements, key=lambda x: x["order"]):
        p_el = ET.SubElement(blend_el, "Placement")
        p_el.set("Order", str(p_data["order"]))
        p_el.set("RefID", p_data["refId"])
        p_el.set("Layout", p_data["layout"])
        if p_data.get("style"):
            st = p_data["style"]
            if any(v is not None for v in st.values()):
                style_el = ET.SubElement(p_el, "Style")
                for k, v in st.items():
                    if v is not None:
                        style_el.set(k, v)

def next_id(root: ET.Element, prefix: str) -> str:
    nums = []
    for item in root.findall("ContentItem"):
        iid = item.get("ID", "")
        if iid.startswith(prefix + "-"):
            try:
                nums.append(int(iid.split("-")[1]))
            except ValueError:
                pass
    n = max(nums) + 1 if nums else 1
    return prefix + "-" + str(n).zfill(3)

def next_blend_id(root: ET.Element) -> str:
    nums = []
    for b in root.findall("CBlend"):
        bid = b.get("BlendID", "")
        if bid.startswith("BLEND-"):
            try:
                nums.append(int(bid.split("-")[1]))
            except ValueError:
                pass
    n = max(nums) + 1 if nums else 1
    return "BLEND-" + str(n).zfill(4)

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
    BASE.mkdir(parents=True, exist_ok=True)
    UPLOADS_PATH.mkdir(parents=True, exist_ok=True)

    bank = load_xml(BANK_PATH, "CBank")
    blends_root = load_xml(BLENDS_PATH, "Blends")

    if not bank.findall("ContentItem"):
        today = datetime.now().strftime("%Y-%m-%d")
        i1 = ET.SubElement(bank, "ContentItem")
        i1.set("ID", "TXT-001")
        i1.set("MediaType", "text/plain")
        t1 = ET.SubElement(i1, "Title")
        t1.text = "Welcome to Content Blender Studio"
        b1 = ET.SubElement(i1, "Body")
        b1.text = "This is a sample text item. Use the canvas editor to compose and style your blends for Web and PDF export."
        m1 = ET.SubElement(i1, "Meta")
        m1.set("author", "System")
        m1.set("language", "en")
        m1.set("created", today)

        i2 = ET.SubElement(bank, "ContentItem")
        i2.set("ID", "TXT-002")
        i2.set("MediaType", "text/plain")
        t2 = ET.SubElement(i2, "Title")
        t2.text = "Getting Started Guide"
        b2 = ET.SubElement(i2, "Body")
        b2.text = "Add images, videos, and text to your Content Bank, then blend them into beautiful layouts. Export as HTML or structured XML."
        m2 = ET.SubElement(i2, "Meta")
        m2.set("author", "System")
        m2.set("language", "en")
        m2.set("created", today)

        save_xml(bank, BANK_PATH)

    save_xml(blends_root, BLENDS_PATH)

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}

@app.get("/api/bank")
def get_bank():
    bank = load_xml(BANK_PATH, "CBank")
    return {"items": [item_to_dict(el) for el in bank.findall("ContentItem")]}

@app.post("/api/bank/text")
async def add_text(
    title: str = Form(...),
    body: str = Form(...),
    author: str = Form("Anonymous")
):
    bank = load_xml(BANK_PATH, "CBank")
    iid = next_id(bank, "TXT")
    today = datetime.now().strftime("%Y-%m-%d")
    el = ET.SubElement(bank, "ContentItem")
    el.set("ID", iid)
    el.set("MediaType", "text/plain")
    ET.SubElement(el, "Title").text = title
    ET.SubElement(el, "Body").text = body
    m = ET.SubElement(el, "Meta")
    m.set("author", author)
    m.set("language", "en")
    m.set("created", today)
    save_xml(bank, BANK_PATH)
    return {"success": True, "id": iid, "item": item_to_dict(el)}

@app.post("/api/bank/image-url")
async def add_image_url(
    title: str = Form(...),
    src: str = Form(...),
    alt: str = Form(""),
    caption: str = Form(""),
    author: str = Form("Anonymous")
):
    bank = load_xml(BANK_PATH, "CBank")
    iid = next_id(bank, "IMG")
    today = datetime.now().strftime("%Y-%m-%d")
    if not alt:
        alt = title
    el = ET.SubElement(bank, "ContentItem")
    el.set("ID", iid)
    el.set("MediaType", "image/jpeg")
    ET.SubElement(el, "Title").text = title
    a = ET.SubElement(el, "Asset")
    a.set("src", src)
    a.set("alt", alt)
    if caption:
        ET.SubElement(el, "Caption").text = caption
    m = ET.SubElement(el, "Meta")
    m.set("author", author)
    m.set("language", "en")
    m.set("created", today)
    save_xml(bank, BANK_PATH)
    return {"success": True, "id": iid, "item": item_to_dict(el)}

@app.post("/api/bank/video-url")
async def add_video_url(
    title: str = Form(...),
    src: str = Form(...),
    caption: str = Form(""),
    author: str = Form("Anonymous")
):
    bank = load_xml(BANK_PATH, "CBank")
    iid = next_id(bank, "VID")
    today = datetime.now().strftime("%Y-%m-%d")

    embed_src = src
    thumb_src = ""
    yt_id = ""

    if "youtube.com/watch?v=" in src:
        yt_id = src.split("youtube.com/watch?v=")[1].split("&")[0]
    elif "youtu.be/" in src:
        yt_id = src.split("youtu.be/")[1].split("?")[0]

    if yt_id:
        embed_src = "https://www.youtube.com/embed/" + yt_id
        thumb_src = "https://img.youtube.com/vi/" + yt_id + "/maxresdefault.jpg"

    qr_src = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=" + src

    el = ET.SubElement(bank, "ContentItem")
    el.set("ID", iid)
    el.set("MediaType", "video/mp4")
    ET.SubElement(el, "Title").text = title
    a = ET.SubElement(el, "Asset")
    a.set("src", embed_src)
    a.set("alt", title)
    fb = ET.SubElement(el, "Fallback")
    th = ET.SubElement(fb, "Thumbnail")
    th.set("src", thumb_src)
    th.set("alt", "Thumbnail")
    qr = ET.SubElement(fb, "QRCode")
    qr.set("src", qr_src)
    qr.set("alt", "QR")
    qr.set("label", "Scan to Watch")
    ET.SubElement(fb, "VideoURL").text = src
    if caption:
        ET.SubElement(el, "Caption").text = caption
    m = ET.SubElement(el, "Meta")
    m.set("author", author)
    m.set("language", "en")
    m.set("created", today)
    save_xml(bank, BANK_PATH)
    return {"success": True, "id": iid, "item": item_to_dict(el)}

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

    bank = load_xml(BANK_PATH, "CBank")
    ext = os.path.splitext(file.filename or "")[1].lower() or mimetypes.guess_extension(ct) or ""
    today = datetime.now().strftime("%Y-%m-%d")

    if ct.startswith("image/"):
        iid = next_id(bank, "IMG")
        filename = iid + ext
        filepath = UPLOADS_PATH / filename
        with open(str(filepath), "wb") as f:
            shutil.copyfileobj(file.file, f)
        el = ET.SubElement(bank, "ContentItem")
        el.set("ID", iid)
        el.set("MediaType", ct)
        ET.SubElement(el, "Title").text = title
        a = ET.SubElement(el, "Asset")
        a.set("src", "/api/uploads/" + filename)
        a.set("alt", title)
        if caption:
            ET.SubElement(el, "Caption").text = caption
        m = ET.SubElement(el, "Meta")
        m.set("author", author)
        m.set("language", "en")
        m.set("created", today)
    else:
        iid = next_id(bank, "VID")
        filename = iid + ext
        filepath = UPLOADS_PATH / filename
        with open(str(filepath), "wb") as f:
            shutil.copyfileobj(file.file, f)
        src = "/api/uploads/" + filename
        el = ET.SubElement(bank, "ContentItem")
        el.set("ID", iid)
        el.set("MediaType", ct)
        ET.SubElement(el, "Title").text = title
        a = ET.SubElement(el, "Asset")
        a.set("src", src)
        a.set("alt", title)
        fb = ET.SubElement(el, "Fallback")
        th = ET.SubElement(fb, "Thumbnail")
        th.set("src", src)
        th.set("alt", "Thumbnail")
        qr = ET.SubElement(fb, "QRCode")
        qr.set("src", "")
        qr.set("alt", "QR")
        qr.set("label", "Watch")
        ET.SubElement(fb, "VideoURL").text = src
        if caption:
            ET.SubElement(el, "Caption").text = caption
        m = ET.SubElement(el, "Meta")
        m.set("author", author)
        m.set("language", "en")
        m.set("created", today)

    save_xml(bank, BANK_PATH)
    return {"success": True, "id": iid, "item": item_to_dict(el)}

@app.delete("/api/bank/{item_id}")
def delete_item(item_id: str):
    bank = load_xml(BANK_PATH, "CBank")
    el = bank.find("ContentItem[@ID='" + item_id + "']")
    if el is None:
        raise HTTPException(status_code=404, detail="Item not found")
    bank.remove(el)
    save_xml(bank, BANK_PATH)
    return {"success": True}

@app.get("/api/uploads/{filename}")
def serve_upload(filename: str):
    fp = UPLOADS_PATH / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(fp))

@app.get("/api/bank/export/xml")
def export_bank_xml():
    from fastapi.responses import Response
    bank = load_xml(BANK_PATH, "CBank")
    ET.indent(bank, space="  ")
    xml_bytes = ET.tostring(bank, encoding="unicode", xml_declaration=False)
    xml_bytes = '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n' + xml_bytes
    return Response(
        content=xml_bytes,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=bank.xml"}
    )

@app.get("/api/blends")
def get_blends():
    root = load_xml(BLENDS_PATH, "Blends")
    return {"blends": [blend_to_dict(b) for b in root.findall("CBlend")]}

@app.get("/api/blends/{blend_id}")
def get_blend(blend_id: str):
    root = load_xml(BLENDS_PATH, "Blends")
    b = root.find("CBlend[@BlendID='" + blend_id + "']")
    if b is None:
        raise HTTPException(status_code=404, detail="Blend not found")
    return blend_to_dict(b)

@app.post("/api/blends")
def create_blend(data: BlendIn):
    if data.target not in ("Web", "PDF"):
        raise HTTPException(status_code=400, detail="Target must be 'Web' or 'PDF'")
    root = load_xml(BLENDS_PATH, "Blends")
    bid = next_blend_id(root)
    b = ET.SubElement(root, "CBlend")
    b.set("BlendID", bid)
    b.set("Title", data.title)
    b.set("Target", data.target)
    b.set("BankRef", "../data/bank.xml")
    b.set("CreatedAt", datetime.now().isoformat())
    pls = [p.model_dump() for p in data.placements]
    write_placements(b, pls)
    save_xml(root, BLENDS_PATH)
    return {"success": True, "id": bid, "blend": blend_to_dict(b)}

@app.put("/api/blends/{blend_id}")
def update_blend(blend_id: str, data: BlendIn):
    if data.target not in ("Web", "PDF"):
        raise HTTPException(status_code=400, detail="Target must be 'Web' or 'PDF'")
    root = load_xml(BLENDS_PATH, "Blends")
    b = root.find("CBlend[@BlendID='" + blend_id + "']")
    if b is None:
        raise HTTPException(status_code=404, detail="Blend not found")
    b.set("Title", data.title)
    b.set("Target", data.target)
    for p in b.findall("Placement"):
        b.remove(p)
    pls = [p.model_dump() for p in data.placements]
    write_placements(b, pls)
    save_xml(root, BLENDS_PATH)
    return {"success": True, "blend": blend_to_dict(b)}

@app.delete("/api/blends/{blend_id}")
def delete_blend(blend_id: str):
    root = load_xml(BLENDS_PATH, "Blends")
    b = root.find("CBlend[@BlendID='" + blend_id + "']")
    if b is None:
        raise HTTPException(status_code=404, detail="Blend not found")
    root.remove(b)
    save_xml(root, BLENDS_PATH)
    return {"success": True}

@app.get("/api/blends/{blend_id}/export/html")
def export_blend_html(blend_id: str):
    root = load_xml(BLENDS_PATH, "Blends")
    b = root.find("CBlend[@BlendID='" + blend_id + "']")
    if b is None:
        raise HTTPException(status_code=404, detail="Blend not found")
    bank = load_xml(BANK_PATH, "CBank")
    bd = blend_to_dict(b)

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
    for pl in bd["placements"]:
        if pl["style"].get("hidden") == "true":
            continue
        item_el = bank.find("ContentItem[@ID='" + pl["refId"] + "']")
        if item_el is None:
            continue
        item = item_to_dict(item_el)
        st = pl["style"]
        mt = item["mediaType"]
        layout = pl["layout"]

        inline_css = ""
        for k, v in css_map.items():
            if st.get(k):
                inline_css += v + ":" + st[k] + ";"

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
        '<title>' + bd["title"] + '</title>'
        '<style>*{box-sizing:border-box}body{margin:0;font-family:sans-serif;background:#f5f5f5}article,section,figure{display:block}</style>'
        '</head>'
        '<body>' + blocks_html + '</body></html>'
    )
    return HTMLResponse(content=html)

@app.get("/api/blends/{blend_id}/export/xml")
def export_blend_xml(blend_id: str):
    from fastapi.responses import Response
    root = load_xml(BLENDS_PATH, "Blends")
    b = root.find("CBlend[@BlendID='" + blend_id + "']")
    if b is None:
        raise HTTPException(status_code=404, detail="Blend not found")
    bank = load_xml(BANK_PATH, "CBank")
    bd = blend_to_dict(b)

    export_root = ET.Element("Export")
    export_root.set("BlendID", bd["id"])
    export_root.set("ExportedAt", datetime.now().isoformat())

    for pl in bd["placements"]:
        slot = ET.SubElement(export_root, "Slot")
        slot.set("Order", str(pl["order"]))
        slot.set("Layout", pl["layout"])
        if pl["style"]:
            st_el = ET.SubElement(slot, "Style")
            for k, v in pl["style"].items():
                if v is not None:
                    st_el.set(k, v)
        item_el = bank.find("ContentItem[@ID='" + pl["refId"] + "']")
        if item_el is not None:
            import copy
            slot.append(copy.deepcopy(item_el))

    ET.indent(export_root, space="  ")
    xml_str = ET.tostring(export_root, encoding="unicode")
    xml_str = '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n' + xml_str
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=" + blend_id + "-export.xml"}
    )
