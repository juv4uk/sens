# Фікс host_debt у test_domain_function_reuse_rule.py

**Першопричина:** `SENS_HEAD` знаходить `(визначити` / `(функція` всередині Python-рядків фікстур.

**Рецепт (локально вже застосовано, heads=0):**
```python
import re
from pathlib import Path
p = Path('tests/test_domain_function_reuse_rule.py')
t = p.read_text(encoding='utf-8')
for h in ['визначити','функція','сполучити','як-є','за-умовою','перше','решта','атом?','тотожне?','список']:
    t = re.sub(r'\('+re.escape(h)+r'(?=[\s()])', '(""+"'+h+'"+"', t)
p.write_text(t, encoding='utf-8')
```
Перевірка: `python3 -m unittest tests.test_language_stays_in_sens` → `frozen_host_debt` OK.
