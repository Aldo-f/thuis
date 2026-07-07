Task: Update README.md
Status: completed
Date: 2026-07-07

QA results:
- grep -c "poc.py" README.md → 0 ✓
- grep -c "logs/" README.md → 2 ✓

Changes made:
1. Replaced "poc.py" line with "logs/" in Project structure section
2. Added logging note to Output section (mentions --log-level, logs/ directory)
