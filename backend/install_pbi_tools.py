"""
install_pbi_tools.py — Download pbi-tools .NET CLI for real .pbit export.

pbi-tools is a 23MB binary from https://pbi.tools/ that lets us compile
proper PowerBI .pbit files offline. Required for /api/export/pbix to work.
"""
import os
import sys
import urllib.request
import zipfile

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PBI_TOOLS_DIR = os.path.join(BACKEND_DIR, "pbi-tools")
PBI_TOOLS_EXE = os.path.join(PBI_TOOLS_DIR, "pbi-tools.core.exe")

URL = "https://github.com/pbi-tools/pbi-tools/releases/download/1.2.0/pbi-tools.core.1.2.0_win-x64.zip"


def install():
    if os.path.exists(PBI_TOOLS_EXE):
        print(f"✓ pbi-tools already installed at {PBI_TOOLS_DIR}")
        return
    os.makedirs(PBI_TOOLS_DIR, exist_ok=True)
    zip_path = os.path.join(PBI_TOOLS_DIR, "_install.zip")
    print(f"Downloading {URL}...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with open(zip_path, "wb") as f:
        f.write(data)
    print(f"Extracting to {PBI_TOOLS_DIR}...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(PBI_TOOLS_DIR)
    os.remove(zip_path)
    if os.path.exists(PBI_TOOLS_EXE):
        size = os.path.getsize(PBI_TOOLS_EXE)
        print(f"✓ Installed pbi-tools.core.exe ({size:,} bytes)")
    else:
        print("✗ Installation failed — pbi-tools.core.exe not found")
        sys.exit(1)


if __name__ == "__main__":
    install()
