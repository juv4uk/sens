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
- `failed-install` — спроба установки не завершилася verified probe.

Жоден із цих станів не додає SID, не змінює значення SID, не нормалізує
foreign truth/result domain і не запускає silent fallback до іншого island.

## Межа v1

Поточний v1 підтримує read-only `plan`, спостереження `status` та явний
`install --dry-run`/`install --apply` для локальних `file://` і HTTP(S)
release-артефактів. Download має timeout, працює через тимчасовий файл,
а перед публікацією артефакт читається повністю і SHA-256 порівнюється
з manifest, а versioned directory публікується транзакційно; повторний запуск
для того самого перевіреного артефакту є ідемпотентним. Package-manager
package-manager виклик і license acceptance ще не виконуються; для таких
записів installer показує план. Bounded executable probe підтримується для
manifest entrypoint і повертає `available` або `probe-failed`.
