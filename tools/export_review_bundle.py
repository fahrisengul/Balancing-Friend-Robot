import json
import os
import sys
from datetime import datetime

# proje kökünden çalıştırılacağını varsayar
from memory.memory_manager import MemoryManager


def main():
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    mm = MemoryManager()
    bundle = mm.export_review_bundle(session_id=session_id, limit=limit)

    out_dir = "review_exports"
    os.makedirs(out_dir, exist_ok=True)

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = session_id if session_id else "latest"
    out_path = os.path.join(out_dir, f"review_bundle_{suffix}_{stamp}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    print(f">>> Review bundle written: {out_path}")


if __name__ == "__main__":
    main()
