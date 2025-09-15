import sys
from pathlib import Path

# Add project root to path so we can import src
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.aruco_detector.detector import ArUcoDetector

d = ArUcoDetector()
for tid in d.template_configs:
    d.current_template = tid
    d.current_template_config = d.template_configs[tid]
    print("\nTemplate", tid)
    print("Resolved mask path:", d.get_template_mask_path())
