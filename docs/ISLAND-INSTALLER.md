# Встановлення execution islands

`my-lisp` зберігає свою семантику та SID у language registry. Execution
islands — Common Lisp, Prolog, CLIPS і Datalog — є окремими runtimes, які
можна підготувати для виконання, але не можна «встановити в семантику».

## План без побічних дій

```bash
my-lisp islands plan --manifest islands-manifest-v1.json --with prolog,clips
my-lisp islands status --manifest islands-manifest-v1.json
```

`plan` лише показує версію, provider, provenance, license, platform і, для
release artifact, SHA-256. Він не завантажує файлів і не запускає package
manager.

`status` описує capability observation:

- `available` — runtime встановлений і пройшов bounded availability probe;
- `absent` — target підтриманий manifest, але runtime ще не встановлений;
- `unsupported` — для target немає verified способу установки;
- `installing` — транзакція ще не завершила atomic publication;
- `failed-install` — download/checksum/license/publish етап завершився помилкою;
- `probe-failed` — verified artifact опублікований, але bounded availability probe не пройдено.

Жоден із цих станів не додає SID, не змінює значення SID, не нормалізує
foreign truth/result domain і не запускає silent fallback до іншого island.

## Межа v1

Поточний v1 підтримує read-only `plan`, спостереження `status` та явний
`install --dry-run`/`install --apply` для локальних `file://` і HTTP(S)
release-артефактів формату `raw-binary`. Download має timeout, працює через
тимчасовий файл, а перед публікацією артефакт читається повністю і SHA-256
порівнюється з manifest. Versioned directory публікується транзакційно;
повторний або конкурентний запуск для того самого перевіреного артефакту
не перезаписує коректну інсталяцію.

Якщо manifest позначає ліцензію як таку, що потребує явного прийняття,
`install --apply` вимагає `--accept-license <island-key[,island-key...]>`
**до download**. Відмова або відсутність acceptance дає `failed-install` і
не створює verified runtime. Package-manager providers не запускаються
автоматично: installer явно повідомляє, що потрібна зовнішня дія, без silent
fallback. Bounded executable probe запускається після atomic publication;
його timeout/non-zero/missing executable дає `probe-failed`, але verified
artifact не видаляється і не перетворюється на semantic failure.
