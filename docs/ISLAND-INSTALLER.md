# Встановлення execution islands

`my-lisp` зберігає свою семантику та SID у language registry. Execution
islands — Common Lisp, Prolog, CLIPS і Datalog — є окремими runtimes, які
можна підготувати для виконання, але не можна «встановити в семантику».

## Один автоматичний шлях

Після встановлення самого `my-lisp` достатньо:

```bash
my-lisp install --profile four-kernel
```

Без `--manifest` CLI сам завантажує останній release manifest з GitHub Release.
Без `--root` використовується platform data directory користувача.

Linux автоматично використовує `apt-get` через `sudo`, коли це потрібно.
Windows автоматично запускає pinned release MSI/NSIS assets у тихих режимах.
Datalog є embedded kernel і окремо не завантажується.

Installer не вимагає ручного `curl`, `apt`, `winget` або копіювання runtime.
Release assets проходять SHA-256 verification перед установкою, а після
встановлення кожен runtime проходить bounded availability probe.

## Що саме встановлюється

Профіль `four-kernel` містить чотири ядра:

- Common Lisp — SBCL runtime; Linux через distro package, Windows через pinned MSI.
- Prolog — SWI-Prolog; Linux через distro package, Windows через pinned official executable.
- CLIPS — Linux через shared-library development package, Windows через pinned 64-bit official runtime archive that contains the shared library.
- Datalog — вбудоване ядро my-lisp. Воно не завантажується окремим архівом: той самий installer-профіль `four-kernel` провізіонує його як частину дистрибутива, записує verified install record і переводить transactional state у `available`.

Відсутній або невірно перевірений runtime не маскується під `available`.
Installer fail-closed і не підміняє один island іншим.

## Перевірка

```bash
my-lisp islands plan --profile four-kernel
my-lisp islands status
```

`plan` не має побічних дій. `status` лише спостерігає capability:
`available`, `absent`, `unsupported` або `probe-failed`.

Для CI та локальних тестів залишається явний `--manifest` та `--root`.
Fixture manifests можуть містити `file://` assets; release manifest має pinned
SHA-256 для кожного `release-asset`. Source manifest у репозиторії є шаблоном:
release workflow обчислює відсутній checksum CLIPS і публікує вже повністю
перевірений manifest.

Installation ≠ semantic admission: встановлення runtime ніколи не створює,
не змінює і не перепризначає SID, не нормалізує foreign truth/result domains
і не додає semantic authority.
