"""Create all ten 50-row AI-assisted gold authoring batches."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "data" / "evaluation" / "gold_v0.1.0"


def main() -> None:
    combined = []
    for start in range(1, 501, 50):
        subprocess.run([
            sys.executable, str(ROOT / "scripts" / "create_gold_batch_draft.py"),
            "--start", str(start), "--count", "50"
        ], check=True)
        end = start + 49
        path = GOLD_DIR / f"gold_batch_{start:03d}_{end:03d}_draft.jsonl"
        combined.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    output = GOLD_DIR / "gold_500_ai_draft.jsonl"
    with output.open("w", encoding="utf-8") as handle:
        for row in combined:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Created {len(combined)} drafts: {output}")


if __name__ == "__main__":
    main()

