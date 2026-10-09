"""Write version_info.txt (Windows file properties) from the package version."""

import re
import sys
from pathlib import Path

here = Path(__file__).parent
init = (here / "../../src/yt_downloader/__init__.py").read_text(encoding="utf-8")
version = re.search(r'__version__ = "([^"]+)"', init)[1]
parts = (version.split(".") + ["0"] * 4)[:4]
nums = ", ".join(str(int(re.match(r"\d+", p)[0])) for p in parts)

(here / "version_info.txt").write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers=({nums}), prodvers=({nums})),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'THE VOID PROTOCOL'),
      StringStruct('FileDescription', 'YT Downloader'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('ProductName', 'YT Downloader'),
      StringStruct('ProductVersion', '{version}'),
      StringStruct('LegalCopyright', '(c) THE VOID PROTOCOL. MIT License.'),
    ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])]),
  ],
)
""", encoding="utf-8")
print(version)
sys.exit(0)
