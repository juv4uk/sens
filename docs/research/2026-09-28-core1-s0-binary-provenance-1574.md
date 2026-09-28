# #1574 — відтворюваний S0 binary provenance для Core1

**Дата:** 2026-09-28
**Статус:** bounded research + narrow CI/manifest repair
**Seed:** `juv4uk/mccarthy-eval@6031f92652066825a245c806c0773e9e524257bd`

## Питання

Чи може `binary-sha256` лишатися byte-exact provenance witness для S0, якщо
один і той самий pinned assembly source збирається різними host toolchains?

Відповідь: **так, але лише всередині явно pinned build closure**.

## Негативний контроль

Pinned source:

```text
mccarthy-kernel.s
sha256 20bdd714a4072cd45ce782bb0b4597a1ff3e96b35624ff86188fb7bb3f455cdd
```

Той самий build command дав різні ELF на цій самій фізичній машині:

- Ubuntu GCC 13.3 / binutils 2.42 → `30f903e15ab0...`
- Guix profile GCC 16.1 / binutils 2.44 → `991a6ab086f3...`

Різниця не обмежена build-id metadata. `.rodata` і `.data` збіглися
побайтово, але `.text` та `.eh_frame` мали різні SHA-256. Dynamic loader
також різний.
## Позитивний контроль

Репозиторій уже має ecosystem-wide Guix pin у `channels.scm`:

```text
guix commit 5375f33fd48ffc3b39ecc1c5993e299258a043d8
```

На цьому channel `gcc-toolchain` дає GCC 16.1.0 / glibc 2.41.

Два незалежні запуски `guix time-machine -C channels.scm -- shell gcc-toolchain -- gcc ...` дали однаковий artifact:

```text
3283cec94edb4211f2aaa4fee5d52c4f9b6add72b1d1db36c142788bf548cfa0
3283cec94edb4211f2aaa4fee5d52c4f9b6add72b1d1db36c142788bf548cfa0
```

Тобто byte-exact hash є відтворюваним, коли build closure справді pinned.

## Найменший чесний контракт

S0 provenance має дві окремі осі:

1. **source identity** — seed repo commit + source SHA-256; не залежить від host;
2. **artifact identity** — binary SHA-256, дійсний лише разом із declared
   `guix-channel-commit`, package і target scope.

Не послаблюємо source pin. Не оголошуємо два ELF semantic-equivalent лише тому,
що обидва проходять bootstrap witness.
## Narrow repair

`contracts/core1-generation-manifest.lisp` тепер фіксує build system, exact
Guix channel commit, package, build command, artifact scope і byte-exact SHA-256.

`.github/workflows/core1-s0.yml` збирає S0 через той самий pinned `guix time-machine`
і перевіряє closure metadata разом із виміряним artifact hash.

## Межі доказу

- Доведено відтворюваність двох локальних незалежних builds на pinned Guix channel.
- CI має окремо підтвердити той самий hash на self-hosted Guix runner.
- Це не доводить semantic equivalence між artifacts із різних closures.
- Це не змінює SENS/Core1 semantics; змінюється лише provenance discipline.
