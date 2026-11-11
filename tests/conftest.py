import sys
from pathlib import Path

# Add src/ to the Python path so tests can import taskcore
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))