"""
BaseX Database Module for Content Blender Studio
Handles all database operations for content bank and blends
"""

from basexclient import BaseXClient
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import xml.etree.ElementTree as ET

# ─── Configuration ───────────────────────────────────────────────────────────

BASEX_HOST = os.getenv("BASEX_HOST", "localhost")
BASEX_PORT = int(os.getenv("BASEX_PORT", "1984"))
BASEX_USER = os.getenv("BASEX_USER", "admin")
BASEX_PASS = os.getenv("BASEX_PASS", "admin")

BANK_DB = "content_bank"
BLENDS_DB = "content_blends"

# ─── Connection Manager ──────────────────────────────────────────────────────

class BaseXConnection:
    """Context manager for BaseX connections"""
    
    def __init__(self):
        self.client = None
    
    def __enter__(self):
        self.client = BaseXClient(BASEX_HOST, BASEX_PORT)
        self.client.connect(BASEX_USER, BASEX_PASS)
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

# ─── Database Initialization ─────────────────────────────────────────────────

def init_databases():
    """Initialize BaseX databases and seed with sample data"""
    try:
        with BaseXConnection() as client:
            # Create banks database
            try:
                client.execute(f"DROP DB {BANK_DB}")
            except:
                pass
            
            bank_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<CBank>
    <ContentItem ID="TXT-001" MediaType="text/plain">
        <Title>Welcome to Content Blender Studio</Title>
        <Body>This is a sample text item. Use the canvas editor to compose and style your blends for Web and PDF export.</Body>
        <Meta author="System" language="en" created="2026-04-02"/>
    </ContentItem>
    <ContentItem ID="TXT-002" MediaType="text/plain">
        <Title>Getting Started Guide</Title>
        <Body>Add images, videos, and text to your Content Bank, then blend them into beautiful layouts. Export as HTML or structured XML.</Body>
        <Meta author="System" language="en" created="2026-04-02"/>
    </ContentItem>
</CBank>'''
            
            client.execute(f"CREATE DB {BANK_DB}")
            client.execute(f"ADD TO {BANK_DB} <root>{bank_xml}</root>")
            
            # Create blends database
            try:
                client.execute(f"DROP DB {BLENDS_DB}")
            except:
                pass
            
            blends_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Blends/>'''
            
            client.execute(f"CREATE DB {BLENDS_DB}")
            client.execute(f"ADD TO {BLENDS_DB} <root>{blends_xml}</root>")
            
            print(f"✓ BaseX databases initialized: {BANK_DB}, {BLENDS_DB}")
    except Exception as e:
        print(f"BaseX initialization error: {e}")
        raise

def check_databases():
    """Check if databases exist, create if not"""
    with BaseXConnection() as client:
        try:
            client.execute(f"OPEN {BANK_DB}")
            client.execute(f"OPEN {BLENDS_DB}")
        except:
            init_databases()

# ─── Content Item Operations ─────────────────────────────────────────────────

def get_all_items() -> List[Dict[str, Any]]:
    """Retrieve all content items from bank"""
    with BaseXConnection() as client:
        result = client.query(f'''
            for $item in db:open("{BANK_DB}")//ContentItem
            return $item
        ''').execute()
        
        items = []
        for item_xml in parse_query_results(result):
            items.append(item_to_dict(item_xml))
        return items

def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve specific content item"""
    with BaseXConnection() as client:
        result = client.query(f'''
            for $item in db:open("{BANK_DB}")//ContentItem[@ID="{item_id}"]
            return $item
        ''').execute()
        
        if result:
            item_xml = ET.fromstring(f"<root>{result}</root>")[0]
            return item_to_dict(item_xml)
    return None

def add_text_item(title: str, body: str, author: str = "Anonymous") -> tuple:
    """Add text item to bank"""
    item_id = get_next_id("TXT")
    today = datetime.now().strftime("%Y-%m-%d")
    
    with BaseXConnection() as client:
        update_query = f'''
            let $item := 
                <ContentItem ID="{item_id}" MediaType="text/plain">
                    <Title>{escape_xml(title)}</Title>
                    <Body>{escape_xml(body)}</Body>
                    <Meta author="{escape_xml(author)}" language="en" created="{today}"/>
                </ContentItem>
            return db:add("{BANK_DB}", $item, "/CBank")
        '''
        client.execute(update_query)
        
    item_data = get_item(item_id)
    return item_id, item_data

def add_image_item(title: str, src: str, alt: str, caption: str, author: str = "Anonymous") -> tuple:
    """Add image item to bank"""
    item_id = get_next_id("IMG")
    today = datetime.now().strftime("%Y-%m-%d")
    if not alt:
        alt = title
    
    caption_xml = f"<Caption>{escape_xml(caption)}</Caption>" if caption else ""
    
    with BaseXConnection() as client:
        update_query = f'''
            let $item := 
                <ContentItem ID="{item_id}" MediaType="image/jpeg">
                    <Title>{escape_xml(title)}</Title>
                    <Asset src="{escape_xml(src)}" alt="{escape_xml(alt)}"/>
                    {caption_xml}
                    <Meta author="{escape_xml(author)}" language="en" created="{today}"/>
                </ContentItem>
            return db:add("{BANK_DB}", $item, "/CBank")
        '''
        client.execute(update_query)
    
    item_data = get_item(item_id)
    return item_id, item_data

def add_video_item(title: str, src: str, caption: str, author: str = "Anonymous") -> tuple:
    """Add video item to bank"""
    item_id = get_next_id("VID")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # YouTube conversion
    embed_src = src
    thumb_src = ""
    
    if "youtube.com/watch?v=" in src:
        yt_id = src.split("youtube.com/watch?v=")[1].split("&")[0]
        embed_src = f"https://www.youtube.com/embed/{yt_id}"
        thumb_src = f"https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg"
    elif "youtu.be/" in src:
        yt_id = src.split("youtu.be/")[1].split("?")[0]
        embed_src = f"https://www.youtube.com/embed/{yt_id}"
        thumb_src = f"https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg"
    
    qr_src = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={src}"
    caption_xml = f"<Caption>{escape_xml(caption)}</Caption>" if caption else ""
    
    with BaseXConnection() as client:
        update_query = f'''
            let $item := 
                <ContentItem ID="{item_id}" MediaType="video/mp4">
                    <Title>{escape_xml(title)}</Title>
                    <Asset src="{escape_xml(embed_src)}" alt="{escape_xml(title)}"/>
                    <Fallback>
                        <Thumbnail src="{escape_xml(thumb_src)}" alt="Thumbnail"/>
                        <QRCode src="{escape_xml(qr_src)}" alt="QR" label="Scan to Watch"/>
                        <VideoURL>{escape_xml(src)}</VideoURL>
                    </Fallback>
                    {caption_xml}
                    <Meta author="{escape_xml(author)}" language="en" created="{today}"/>
                </ContentItem>
            return db:add("{BANK_DB}", $item, "/CBank")
        '''
        client.execute(update_query)
    
    item_data = get_item(item_id)
    return item_id, item_data

def add_uploaded_item(title: str, src: str, media_type: str, caption: str, author: str = "Anonymous") -> tuple:
    """Add uploaded file item to bank"""
    prefix = "IMG" if media_type.startswith("image/") else "VID"
    item_id = get_next_id(prefix)
    today = datetime.now().strftime("%Y-%m-%d")
    caption_xml = f"<Caption>{escape_xml(caption)}</Caption>" if caption else ""
    
    if media_type.startswith("image/"):
        item_xml = f'''
            <ContentItem ID="{item_id}" MediaType="{media_type}">
                <Title>{escape_xml(title)}</Title>
                <Asset src="{escape_xml(src)}" alt="{escape_xml(title)}"/>
                {caption_xml}
                <Meta author="{escape_xml(author)}" language="en" created="{today}"/>
            </ContentItem>
        '''
    else:  # video
        item_xml = f'''
            <ContentItem ID="{item_id}" MediaType="{media_type}">
                <Title>{escape_xml(title)}</Title>
                <Asset src="{escape_xml(src)}" alt="{escape_xml(title)}"/>
                <Fallback>
                    <Thumbnail src="{escape_xml(src)}" alt="Thumbnail"/>
                    <QRCode src="" alt="QR" label="Watch"/>
                    <VideoURL>{escape_xml(src)}</VideoURL>
                </Fallback>
                {caption_xml}
                <Meta author="{escape_xml(author)}" language="en" created="{today}"/>
            </ContentItem>
        '''
    
    with BaseXConnection() as client:
        update_query = f'db:add("{BANK_DB}", {item_xml}, "/CBank")'
        client.execute(update_query)
    
    item_data = get_item(item_id)
    return item_id, item_data

def delete_item(item_id: str) -> bool:
    """Delete content item from bank"""
    with BaseXConnection() as client:
        client.execute(f'''
            delete node db:open("{BANK_DB}")//ContentItem[@ID="{item_id}"]
        ''')
    return True

def get_next_id(prefix: str) -> str:
    """Generate next item ID"""
    with BaseXConnection() as client:
        result = client.query(f'''
            let $max := max(
                for $item in db:open("{BANK_DB}")//ContentItem[@ID]
                where starts-with($item/@ID, "{prefix}-")
                return xs:integer(substring-after($item/@ID, "{prefix}-"))
            )
            return if ($max) then $max + 1 else 1
        ''').execute()
    
    num = int(result) if result else 1
    return f"{prefix}-{str(num).zfill(3)}"

# ─── Blend Operations ────────────────────────────────────────────────────────

def get_all_blends() -> List[Dict[str, Any]]:
    """Retrieve all blends"""
    with BaseXConnection() as client:
        result = client.query(f'''
            for $blend in db:open("{BLENDS_DB}")//CBlend
            return $blend
        ''').execute()
        
        blends = []
        for blend_xml in parse_query_results(result):
            blends.append(blend_to_dict(blend_xml))
        return blends

def get_blend(blend_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve specific blend"""
    with BaseXConnection() as client:
        result = client.query(f'''
            for $blend in db:open("{BLENDS_DB}")//CBlend[@BlendID="{blend_id}"]
            return $blend
        ''').execute()
        
        if result:
            blend_xml = ET.fromstring(f"<root>{result}</root>")[0]
            return blend_to_dict(blend_xml)
    return None

def create_blend(title: str, target: str, placements: List[Dict]) -> tuple:
    """Create new blend"""
    blend_id = get_next_blend_id()
    created_at = datetime.now().isoformat()
    
    placements_xml = ""
    for p in sorted(placements, key=lambda x: x.get("order", 0)):
        style_xml = ""
        if p.get("style"):
            style_attrs = " ".join([
                f'{k}="{escape_xml(str(v))}"' 
                for k, v in p["style"].items() 
                if v is not None
            ])
            if style_attrs:
                style_xml = f"<Style {style_attrs}/>"
        
        placements_xml += f'''
            <Placement Order="{p.get("order", 0)}" RefID="{p.get("refId", "")}" Layout="{p.get("layout", "body")}">
                {style_xml}
            </Placement>
        '''
    
    blend_xml = f'''
        <CBlend BlendID="{blend_id}" Title="{escape_xml(title)}" Target="{target}" BankRef="../data/bank.xml" CreatedAt="{created_at}">
            {placements_xml}
        </CBlend>
    '''
    
    with BaseXConnection() as client:
        update_query = f'db:add("{BLENDS_DB}", {blend_xml}, "/Blends")'
        client.execute(update_query)
    
    blend_data = get_blend(blend_id)
    return blend_id, blend_data

def update_blend(blend_id: str, title: str, target: str, placements: List[Dict]) -> Dict:
    """Update existing blend"""
    with BaseXConnection() as client:
        # Remove old placements
        client.execute(f'''
            delete node db:open("{BLENDS_DB}")//CBlend[@BlendID="{blend_id}"]/Placement
        ''')
        
        # Update title and target
        client.execute(f'''
            let $blend := db:open("{BLENDS_DB}")//CBlend[@BlendID="{blend_id}"]
            return (
                replace value of node $blend/@Title with "{escape_xml(title)}",
                replace value of node $blend/@Target with "{target}"
            )
        ''')
    
    # Re-insert placements
    for p in sorted(placements, key=lambda x: x.get("order", 0)):
        style_xml = ""
        if p.get("style"):
            style_attrs = " ".join([
                f'{k}="{escape_xml(str(v))}"' 
                for k, v in p["style"].items() 
                if v is not None
            ])
            if style_attrs:
                style_xml = f"<Style {style_attrs}/>"
        
        placement_el = f'''
            <Placement Order="{p.get("order", 0)}" RefID="{p.get("refId", "")}" Layout="{p.get("layout", "body")}">
                {style_xml}
            </Placement>
        '''
        
        with BaseXConnection() as client:
            client.execute(f'''
                let $blend := db:open("{BLENDS_DB}")//CBlend[@BlendID="{blend_id}"]
                return insert node {placement_el} into $blend
            ''')
    
    blend_data = get_blend(blend_id)
    return blend_data

def delete_blend(blend_id: str) -> bool:
    """Delete blend"""
    with BaseXConnection() as client:
        client.execute(f'''
            delete node db:open("{BLENDS_DB}")//CBlend[@BlendID="{blend_id}"]
        ''')
    return True

def get_next_blend_id() -> str:
    """Generate next blend ID"""
    with BaseXConnection() as client:
        result = client.query(f'''
            let $max := max(
                for $blend in db:open("{BLENDS_DB}")//CBlend[@BlendID]
                where starts-with($blend/@BlendID, "BLEND-")
                return xs:integer(substring-after($blend/@BlendID, "BLEND-"))
            )
            return if ($max) then $max + 1 else 1
        ''').execute()
    
    num = int(result) if result else 1
    return f"BLEND-{str(num).zfill(4)}"

# ─── Export Operations ───────────────────────────────────────────────────────

def export_bank_xml() -> str:
    """Export entire bank as XML"""
    with BaseXConnection() as client:
        result = client.query(f'''
            db:open("{BANK_DB}")/CBank
        ''').execute()
    return result

def export_blend_xml(blend_id: str) -> str:
    """Export blend with items as XML"""
    with BaseXConnection() as client:
        result = client.query(f'''
            let $blend := db:open("{BLENDS_DB}")//CBlend[@BlendID="{blend_id}"]
            let $bank := db:open("{BANK_DB}")/CBank
            let $export := 
                <Export BlendID="{blend_id}" ExportedAt="{datetime.now().isoformat()}">
                    {{
                        for $pl in $blend/Placement
                        let $item := $bank/ContentItem[@ID=$pl/@RefID]
                        return 
                            <Slot Order="{{$pl/@Order}}" Layout="{{$pl/@Layout}}">
                                {{if ($pl/Style) then $pl/Style else ()}}
                                {{$item}}
                            </Slot>
                    }}
                </Export>
            return $export
        ''').execute()
    return result

def get_blend_with_items(blend_id: str) -> Dict[str, Any]:
    """Get blend and resolve all referenced items"""
    blend = get_blend(blend_id)
    if not blend:
        return None
    
    # Resolve items for each placement
    for pl in blend["placements"]:
        item = get_item(pl["refId"])
        if item:
            pl["item"] = item
    
    return blend

# ─── Helper Functions ────────────────────────────────────────────────────────

def escape_xml(text: str) -> str:
    """Escape special XML characters"""
    if not text:
        return ""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;"))

def parse_query_results(result: str) -> List[ET.Element]:
    """Parse XQuery results into XML elements"""
    if not result.strip():
        return []
    
    # Wrap results in root element
    wrapped = f"<root>{result}</root>"
    try:
        root = ET.fromstring(wrapped)
        return list(root)
    except:
        return []

def item_to_dict(el: ET.Element) -> Dict[str, Any]:
    """Convert ContentItem XML element to dictionary"""
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

def placement_to_dict(p: ET.Element) -> Dict[str, Any]:
    """Convert Placement XML element to dictionary"""
    style_el = p.find("Style")
    style = dict(style_el.attrib) if style_el is not None else {}
    return {
        "order": int(p.get("Order", 0)),
        "refId": p.get("RefID", ""),
        "layout": p.get("Layout", "body"),
        "style": style
    }

def blend_to_dict(b: ET.Element) -> Dict[str, Any]:
    """Convert CBlend XML element to dictionary"""
    pls = [placement_to_dict(p) for p in b.findall("Placement")]
    pls.sort(key=lambda x: x["order"])
    return {
        "id": b.get("BlendID", ""),
        "title": b.get("Title", ""),
        "target": b.get("Target", "Web"),
        "createdAt": b.get("CreatedAt", ""),
        "placements": pls
    }
