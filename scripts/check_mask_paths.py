import sys
from pathlib import Path

# Add project root to path so we can import src
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.aruco_detector.template_config import TEMPLATE_MARKER_SETS

print("CWD:", Path.cwd())
print("sys.executable:", sys.executable)
print("sys._MEIPASS:", getattr(sys, "_MEIPASS", None))

for tid, cfg in TEMPLATE_MARKER_SETS.items():
    mask_file = cfg.get("mask_file")
    print("\nTemplate", tid, "mask_file=", mask_file)
    possible_paths = [
        Path("data/markers/templates") / mask_file,
        Path(__file__).parent.parent / "data/markers/templates" / mask_file,
        Path(sys.executable).parent / "data/markers/templates" / mask_file,
        Path(sys.executable).parent / "src/data/markers/templates" / mask_file,
    ]
    for p in possible_paths:
        print("  ->", p, "exists=", p.exists())
    # alt filename
    if "mask" in tid or mask_file:
        alt_filename = f"mask{tid[-1]}_final.png"
        print("  alt filename:", alt_filename)
        for base in possible_paths:
            p = base.parent / alt_filename
            print("    alt ->", p, "exists=", p.exists())

# Also list files in data/markers/templates
print("\nListing data/markers/templates:")
for p in Path("data/markers/templates").glob("*"):
    print("  ", p.name)
