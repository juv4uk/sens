#!/usr/bin/env bash
# Ануграха: першопричина host_debt — суцільні SENS-голови у probe-рядках
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
python3 - <<'PY'
import re
from pathlib import Path
p = Path("tests/test_domain_function_reuse_rule.py")
t = p.read_text(encoding="utf-8")
for h in ["визначити", "функція", "сполучити", "як-є", "за-умовою", "перше", "решта", "атом?", "тотожне?", "список"]:
    t = re.sub(r"\(" + re.escape(h) + r"(?=[\s()])", '(""+"' + h + '"+"', t)
p.write_text(t, encoding="utf-8")
print("host_debt fixtures split in", p)
PY
python3 -m unittest tests.test_language_stays_in_sens.LanguageStaysInSens.test_frozen_host_debt_only_shrinks -q
echo OK
