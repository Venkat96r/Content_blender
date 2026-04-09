# BaseX Integration Setup Guide

## Overview

Your Content Blender application has been integrated with **BaseX**, a native XML database. This replaces the file-based XML storage system with a robust, queryable database backend.

## Benefits

✅ **Better Performance** - XQuery optimization for large datasets  
✅ **Transactional** - ACID compliance for data integrity  
✅ **Scalable** - Handles large XML documents efficiently  
✅ **Queryable** - Full XQuery/XPath support for complex queries  
✅ **Centralized** - Single database for bank and blends  

## Prerequisites

- **BaseX Server** (latest version)
- **Python 3.8+**

## Installation Steps

### 1. Install BaseX Server

#### macOS (Homebrew)
```bash
brew install basex
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install basex
```

#### Windows
Download from [BaseX Official Download](https://basex.org/download/)

### 2. Start BaseX Server

#### macOS/Linux
```bash
# Start BaseX server (listens on localhost:1984 by default)
basexhttp &

# Or use:
basex -S
```

#### Windows
```cmd
basexhttp.bat
# Or
basex -S
```

The server should print:
```
[INFO] HTTP Server started in 123ms
[INFO] Server was started successfully
```

### 3. Install Python Dependencies

```bash
cd backend/
pip install -r requirements.txt
```

This will install:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `basex-client` - Python client for BaseX
- `python-dotenv` - Environment variable management
- Other dependencies (pydantic, lxml, etc.)

### 4. Configure Environment

Copy the example configuration:
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` if you changed BaseX defaults:
```env
BASEX_HOST=localhost
BASEX_PORT=1984
BASEX_USER=admin
BASEX_PASS=admin
```

### 5. Run the Application

```bash
# From the root directory
python start.py
```

The backend will:
1. Connect to BaseX server
2. Initialize databases (`content_bank`, `content_blends`)
3. Seed with sample data
4. Start on `http://localhost:8000`

## Database Structure

### `content_bank` Database
```xml
<CBank>
  <ContentItem ID="TXT-001" MediaType="text/plain">
    <Title>...</Title>
    <Body>...</Body>
    <Meta author="..." language="..." created="..."/>
  </ContentItem>
  ...
</CBank>
```

### `content_blends` Database
```xml
<Blends>
  <CBlend BlendID="BLEND-0001" Title="..." Target="Web" CreatedAt="...">
    <Placement Order="1" RefID="TXT-001" Layout="body">
      <Style width="100%" padding="16px"/>
    </Placement>
    ...
  </CBlend>
</Blends>
```

## API Endpoints (Unchanged)

All frontend API endpoints remain the same:
- `GET /api/bank` - List all content items
- `POST /api/bank/text` - Add text content
- `POST /api/bank/image-url` - Add image from URL
- `POST /api/bank/video-url` - Add video
- `POST /api/bank/upload` - Upload files
- `DELETE /api/bank/{id}` - Delete item
- `GET /api/blends` - List blends
- `POST /api/blends` - Create blend
- `PUT /api/blends/{id}` - Update blend
- `DELETE /api/blends/{id}` - Delete blend
- `GET /api/blends/{id}/export/html` - Export as HTML
- `GET /api/blends/{id}/export/xml` - Export as XML

## Troubleshooting

### BaseX Connection Error
```
Error: Could not connect to BaseX server
```

**Solution:**
1. Check if BaseX server is running: `basex -S`
2. Verify host/port in `.env` match server settings
3. Check firewall rules for port 1984

### Database Not Found
```
Error: Database ... not found
```

**Solution:**
Databases are auto-created on first run. If missing:
1. Delete `.env` and restart (forces re-initialization)
2. Or manually create databases:
```bash
basex
# In BaseX GUI, run:
# CREATE DB content_bank
# CREATE DB content_blends
```

### Permission Denied
```
Error: User was not recognized
```

**Solution:**
- Default credentials are `admin/admin`
- Change in BaseX admin panel if needed
- Update `.env` with new credentials

### Port Already in Use
```
Error: Address already in use: 1984
```

**Solution:**
```bash
# Kill existing process
lsof -i :1984  # macOS/Linux
kill -9 <PID>

# Or use different port in .env
BASEX_PORT=1985
```

## Backup & Restore

### Backup Databases
```bash
# Export bank data
curl http://localhost:8000/api/bank/export/xml > backup_bank.xml

# Export blends
curl 'http://localhost:8000/api/blends' | jq
```

### Restore from Backup
1. Stop the server
2. Drop databases: `basex DROP DB content_bank`
3. Re-start server (auto-initializes with defaults)
4. Restore via API endpoints

## Performance Tips

1. **Connection Pooling** - The client maintains persistent connections
2. **Query Optimization** - XQuery is pre-optimized for indexing
3. **Indexes** - BaseX auto-creates indexes on element IDs
4. **Lazy Loading** - Items are loaded on-demand, not all at once

## Migration from File-Based Storage

If migrating from old XML files:

1. Back up old files
2. Export content via API
3. Delete `backend/data/bank.xml` and `backend/data/blends.xml`
4. Restart backend (creates databases)
5. Re-import data through API endpoints

## Advanced: Custom BaseX Queries

You can add powerful XQuery operations in `backend/basex_db.py`. Examples:

```python
# Find items by author
client.query(f'''
    for $item in db:open("{BANK_DB}")//ContentItem
    where $item/Meta/@author = "John"
    return $item/Title/text()
''').execute()

# Full-text search
client.query(f'''
    for $item in db:open("{BANK_DB}")//ContentItem
    where contains($item//text(), "keyword")
    return $item/@ID
''').execute()
```

## Support

- **BaseX Documentation**: https://docs.basex.org/
- **BaseX Client Docs**: https://basex.org/articles/client-api/
- **XQuery Tutorials**: https://www.w3schools.com/xml/xquery_intro.asp

---

**Note:** Upload files are still stored locally in `backend/data/uploads/`. Only metadata is stored in BaseX.
