from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FILE_LIFECYCLE_SRC = REPO_ROOT / "packages" / "file-lifecycle" / "src"
if str(FILE_LIFECYCLE_SRC) not in sys.path:
    sys.path.insert(0, str(FILE_LIFECYCLE_SRC))

from atlas_file_lifecycle import (  # noqa: E402
    FileItem,
    FileMetadata,
    FileReference,
    FileSource,
    RetentionIntent,
    compare_file_lifecycle,
    project_file_item,
)


def main() -> int:
    item = FileItem(
        id="synthetic-upload-1",
        source=FileSource("uploaded", "synthetic intake"),
        metadata=FileMetadata(
            original_name="orders.xlsx",
            display_name="orders.xlsx",
            extension=".xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size_bytes=2048,
            checksum="sha256:synthetic",
        ),
    )
    available = item.transition_to(
        "accepted",
        reference=FileReference("local", "synthetic://uploads/orders.xlsx", display_locator="orders.xlsx"),
    ).transition_to("available", retention=RetentionIntent("retained", reason="synthetic example"))

    primary = {
        "id": "synthetic-upload-1",
        "source_kind": "uploaded",
        "state": "available",
        "reference_kind": "local",
        "locator": "synthetic://uploads/orders.xlsx",
        "display_locator": "orders.xlsx",
        "original_name": "orders.xlsx",
        "display_name": "orders.xlsx",
        "extension": ".xlsx",
        "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "size_bytes": 2048,
        "checksum": "sha256:synthetic",
        "issue_codes": (),
    }
    diff = compare_file_lifecycle(primary, available, explained_fields=("source_label", "state_reason", "retention_mode", "retention_reason", "issue_severities"))

    print(
        json.dumps(
            {
                "file": project_file_item(available),
                "shadow": {
                    "status": diff.status,
                    "unexplained_differences": len(diff.unexplained_differences),
                    "lost_metadata": len(diff.lost_metadata),
                    "lost_issues": len(diff.lost_issues),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
