"""Make the repository's experiment namespace importable with the pytest CLI."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
