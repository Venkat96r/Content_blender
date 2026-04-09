#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "  Content Blender - BaseX Integration Quick Start"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if BaseX is running
echo "🔍 Checking for BaseX server..."
if nc -z localhost 1984 2>/dev/null; then
    echo "✅ BaseX server is running on port 1984"
else
    echo "❌ BaseX server is NOT running"
    echo ""
    echo "Start BaseX server in another terminal:"
    echo "  macOS/Linux:  basex -S"
    echo "  Windows:      basexhttp.bat"
    echo ""
    exit 1
fi

echo ""
echo "📦 Installing Python dependencies..."
cd backend/
pip install -r requirements.txt

echo ""
echo "⚙️  Creating .env configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
else
    echo "✅ .env already exists"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "   python start.py"
echo ""
echo "📚 For detailed setup instructions:"
echo "   See BASEX_SETUP.md"
echo ""
