# D10 — відновлення трьох незлитих міжрепозиторних досліджень (2026-10-09)

## Джерело
- PR #4391 / branch research/d10-linguistic-v1: \`knowledge/d10-crossrepo-linguistic-v1.json\` (9 rows).
- PR #4393 / branch research/d10-4301-physical-donor-scan: \`knowledge/d10-crossrepo-domain-v1.json\` (11 rows).
- PR #4399 / branch research/d10-knowledge-tooling-v1: \`knowledge/d10-crossrepo-knowledge-tooling-v1.json\` (8 rows).

Старі гілки відстали від main на сотні комітів. Лише три ізольовані дослідницькі JSON перенесено на **свіжий main**, без переливання старого історичного стану доменів.

## Облік
- Це 28 **donor evidence rows**, не +28 функцій D10.
- Поле \`decision=SELECT\` у старому мовознавчому звіті означає лише авторську *рекомендацію*, не факт включення у канонічний \`knowledge/d10-v1-semantic-inventory.json\`.
- Чинний normative count на момент роботи: 625 selected із 1024, 256 selector-law positions, 369 unplaced, 399 unselected, 0 ratified.
- Ні координат, ні бітових resident, ні зміни D1–D9, D2, Text7, T5 немає.

## Чому не пряма merge old branch
Історія комітів \`diverged\` може містити давні, вже переписані канонічні таблиці і не є доказом нових semantics. Перенесено лише джерельні звіти, дані безпечні для окремого рев'ю.

## Наступний власницький review
- Для \`TOKENIZE-SENTENCES\` / \`TOKENIZE-WORDS\`: відрізнити linguistic lexical boundary від \`STRING-SPLIT\`; визначити Text7/лексер ownership.
- Для \`LEMMATIZE-TEXT\`, \`INFLECT-WORD\`, \`MORPHO-SYNTACTIC-TAG\`: source-level behavioral parity, Sanskrit/uk language-independent law і незалежний oracle; чи це D10 universal semantics, чи application/library policy.
- Для physics/knowledge rows — зберегти \`HOLD\`/\`PROJECTION\`/\`MECHANISM-ONLY\`, доки незалежний observable не доведе інакше.
- Канонічний D10 розширюється тільки через окреме source-locked доведення із positive, falsifier, ratified domain duplicate scan, review. D2 — єдиний власник керування мовою.

Виконання guard: \`python3 scripts/check-d10-archived-donors.py --self-test\`.
