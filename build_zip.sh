#!/usr/bin/env bash
# Package the skill folder into malaysian-travel-planner.zip for upload to Claude.
set -euo pipefail
cd "$(dirname "$0")"
rm -f malaysian-travel-planner.zip
find malaysian-travel-planner -name "__pycache__" -type d -prune -exec rm -rf {} +
zip -rq malaysian-travel-planner.zip malaysian-travel-planner -x "*.pyc" -x "*/.DS_Store"
echo "Built malaysian-travel-planner.zip"
