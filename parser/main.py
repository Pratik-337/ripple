import argparse
import json
from pathlib import Path

from parser.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Ripple Code Analysis CLI"
    )

    parser.add_argument(
        "path",
        type=str,
        help="Path to project directory"
    )

    parser.add_argument(
        "--send-backend",
        action="store_true",
        help="Send graph to backend"
    )

    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format"
    )

    args = parser.parse_args()

    output, impacts = run_pipeline(
        Path(args.path),
        send_to_backend=args.send_backend
    )

    if args.format == "json":
        print(json.dumps(output, indent=2))
    else:
        print("\nIMPACT ANALYSIS:")
        for node_id, info in impacts.items():
            print(f"{node_id} (depth={info['depth']}, via={info['via']})")


if __name__ == "__main__":
    main()
