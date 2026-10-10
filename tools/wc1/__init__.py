"""wc1: analysis and rebuild tooling for Warcraft: Orcs & Humans (DOS, v1.22h)."""
import os

ROOT = os.environ.get("WC1_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def path(*p):
    return os.path.join(ROOT, *p)

ORIGINAL_EXE = path("original", "install", "war.exe")
