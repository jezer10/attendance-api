import sys
from pathlib import Path

# .../attendance_api/src/tests/conftest.py -> subir 2 niveles -> .../attendance_api
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
