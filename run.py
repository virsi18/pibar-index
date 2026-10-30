"""
PiBarX - Global Pi Barter Real-Price Index
Launcher Script
"""

import sys
import uvicorn

def main():
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    print("=" * 68)
    print("  PiBarX - Global Pi Barter Real-Price Index")
    print("  Macroeconomic Purchasing Power Parity & Commodity Consensus")
    print("=" * 68)
    print(f"  > Dashboard: {url}")
    print(f"  > Interactive OpenAPI Docs: {url}/docs")
    print(f"  > Stitch AI Design System: Obsidian Parity Terminal")
    print("=" * 68)

    # Launch server with reload=True so changes hot-reload automatically
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()
