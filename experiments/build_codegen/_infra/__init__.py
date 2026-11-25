"""Campaign orchestration infrastructure for Build & Codegen Experiments (E0-E8)."""
import os

CAMPAIGN_ID = "2026-11-25-build-codegen"
MANAGER_SESSION_ID = "346b5272-d421-466b-95ad-67bdb0fc2b62"
MAIN_REPO = "/mnt/data/projects/warcraft-1-decompile"
WT_ROOT = "/mnt/data/projects/warcraft-1-decompile-wt"
STATE_ROOT = "/mnt/data/projects/warcraft-1-decompile-campaign-state"
TELEMETRY_DIR = os.path.join(MAIN_REPO, "docs", "telemetry", "campaigns", CAMPAIGN_ID)
LEDGER_PATH = os.path.join(MAIN_REPO, "docs", "research", "build-codegen", "ledger.json")
