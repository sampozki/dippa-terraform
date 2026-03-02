#!/usr/bin/env python3

import json
import subprocess
import sys
from typing import List, Dict, Any


def load_plan_json(plan_file: str) -> Dict[str, Any]:
    """
    Runs `terraform show -json` against the given plan file
    and returns parsed JSON.
    """
    try:
        result = subprocess.run(
            ["terraform", "show", "-json", plan_file],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: terraform show failed\n{e.stdout}\n{e.stderr}")
        sys.exit(2)

    return json.loads(result.stdout)


def extract_drift(plan_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts resource changes that are not no-op.
    """
    drifts = []

    for rc in plan_json.get("resource_changes", []):
        change = rc.get("change", {})
        actions = change.get("actions", [])

        if actions and actions != ["no-op"]:
            drifts.append({
                "address": rc.get("address"),
                "type": rc.get("type"),
                "actions": actions
            })

    return drifts


def main():
    if len(sys.argv) != 2:
        print("Usage: detect_drift.py <plan.out>")
        sys.exit(1)

    plan_file = sys.argv[1]

    plan_json = load_plan_json(plan_file)
    drifts = extract_drift(plan_json)

    output = {
        "drift_detected": len(drifts) > 0,
        "resource_change_count": len(drifts),
        "resource_changes": drifts
    }

    print(json.dumps(output, indent=2))

    # Exit code convention:
    # 0 = no drift
    # 10 = drift detected
    sys.exit(10 if drifts else 0)


if __name__ == "__main__":
    main()
