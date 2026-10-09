# SENS D10: часовий research-пакет

Це готовий до перенесення в GitHub **дослідницький** пакет з 9 source-pinned визначеннями (5 candidates, 4 HOLD) та незалежними позитивними/негативними референсними прикладами. Прийняття в канонічні 625 selected: **0**. Ратифікацій: **0**.

Для місцевої перевірки: `python3 scripts/check_d10_time_law_review_v2.py` та `python3 -m unittest discover -s tests -p 'test_d10_time_law_review_v2.py' -v`.

Для source SHA + D1-D9/D10 dedup перевірки копіюйте в справжній корінь `sens` та запускайте там. Перевірка прикладів поки незалежна від SENS виконання, не видавати за oracle parity.

### v3: суворий CI, а не фальшивий PASS

Реальна GitHub-перевірка **обов’язково** запускає `--require-checkout`. Раніше відсутність `lib/time.lisp` або `knowledge/d1-d9-foundation.json` / `knowledge/d10-v1-semantic-inventory.json` давала `SKIP` із загальним PASS; тепер CI такого **не пропускає**. Звичайні тести пакета поза репозиторієм лишаються *research fixture only*, не доказом реального SENS-виконання.

- `python3 scripts/check_d10_time_law_review_v2.py` — лише структурна перевірка в окремому пакеті.
- `python3 scripts/check_d10_time_law_review_v2.py --require-checkout` — істинний repository/CI gate, який вимагає джерело й реєстри.
- `.github/workflows/d10-time-review-v2.yml` — workflow для справжнього GitHub checkout.

**Стан коміту:** пакет підготовлений локально, НЕ злитий до GitHub через GitHub `403 secondary rate limit`. Ніякі зміни канонічних лічильників чи 10-бітних координат не виконані.


### Підсумок незалежного аудиту (9 жовтня 2026)

Із підключеного GitHub безпосередньо прочитано `juv4uk/sens/main`:
- `lib/time.lisp` blob `74013e20c0c5abb9a68c62334f40095c29294a53`; точний початок визначення у рядках 9, 73, 82, 91, 114, 134, 185, 198, 213: 9/9.
- `knowledge/d1-d9-foundation.json` blob `09d1d71c39d1484dfd005a5068dbb18b76f0f0d4`;
- `knowledge/d10-v1-semantic-inventory.json` blob `73dd518469f972c55411e004b70b054ba8b3ec86` — 625 selected / 0 ratified; **точних колізій назв: 0**.
- Тотожність семантики проти ратифікованих похідних функцій НЕ доведена; незалежний SENS oracle НЕ запущений. Це research-only пакет.

Критичний ремонт від попереднього v3: новий `.patch` **не містить `__pycache__` / `.pyc`**; `python -O` не може вимкнути research gate. Патч генерувати виключно з шести текстових файлів + цього handoff.
