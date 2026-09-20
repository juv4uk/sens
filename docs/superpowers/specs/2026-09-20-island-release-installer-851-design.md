# #851: release installer для execution islands — дизайн

## Мета

Після встановлення `my-lisp` користувач може окремо планувати, встановлювати
й спостерігати доступність execution islands: Common Lisp, SWI-Prolog, CLIPS
та власних артефактів на кшталт Datalog adapter. Це distribution і capability
layer; він не є semantic layer.

## Незмінні межі

Installer не має права видавати або змінювати SID, нормалізувати foreign
truth/result domains, робити silent fallback між islands чи трактувати
`installed` як semantic admission. Семантика належить registry/Lisp laws;
кожен island лишається незалежним runtime зі своєю ліцензією, версією та
lifecycle.

## Перший зріз CLI

```text
my-lisp islands plan --with prolog,clips
my-lisp islands install --with prolog,clips
my-lisp islands status
```

`plan` є read-only та друкує назву island, версію, provider, platform,
provenance, license та очікувану дію. `install` приймає цей explicit request,
перевіряє platform і artifact checksum, пише versioned install record та не
публікує island як available до успішного bounded probe. `status` повертає
лише observation: `available`, `absent`, `unsupported` або `failed-install`.

## Manifest

Release публікує versioned `islands-manifest-v1.json`. Для кожного island він
має stable key, runtime version, ABI compatibility, ліцензійний notice,
список platform entries та provider.

- `release-asset`: URL, SHA-256, archive format і bounded probe;
- `system-package`: provider (`apt`, `dnf`, `brew`, `winget`), package name,
  expected executable та bounded probe;
- `unsupported`: explicit platform outcome без guessed command.

V1 не завантажує artifact автоматично: `plan` показує намір, `install` є
окремою дією. System-package provenance належить package manager; release
asset provenance — pinned URL і SHA-256.

## Дані на машині

Verified release artifacts лежать у versioned directory нижче
platform data directory, наприклад:

```text
~/.local/share/my-lisp/islands/clips/6.4.2/linux-x86_64/
```

Install record містить manifest digest, artifact digest, runtime version,
platform та час bounded probe. Невдала установка пише failure observation,
але не створює record `available`; partial download залишається поза
verified directory або прибирається.

## Probe та вихідні стани

Probe — лише runtime availability/ABI handshake, наприклад `swipl --version`;
він не запускає semantic suite і не перетворює результат island на my-lisp
value. `available` означає лише, що конкретний runtime доступний. `absent`,
`unsupported` та `failed-install` є чесними й різними станами.

## Верифікація

Перші Rust tests покривають manifest parsing, platform selection, plan without
side effects, SHA-256 mismatch, idempotent verified record та distinct status
states. Перший commit не додає network installer: він створює manifest model,
`plan` та `status` на fixture manifest. Реальне download/install — наступний
малий зріз після review security/provenance boundary.
