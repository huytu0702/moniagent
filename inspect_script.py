from pathlib import Path
path = Path("backend/docs/AI_AGENT_ANALYSIS.md")
lines = path.read_text(encoding="utf-8").splitlines()
anchor = None
for idx,line in enumerate(lines):
    if "detect_update_intent` / `process_update`" in line:
        anchor = idx
        break
if anchor is None:
    raise SystemExit("Anchor not found")
