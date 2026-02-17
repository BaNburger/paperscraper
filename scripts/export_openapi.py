"""Export FastAPI OpenAPI schema to a JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_scraper.api.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export OpenAPI schema from FastAPI app")
    parser.add_argument(
        "--output",
        default="openapi.json",
        help="Output JSON path (default: openapi.json)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Wrote OpenAPI schema to {output_path}")


if __name__ == "__main__":
    main()

