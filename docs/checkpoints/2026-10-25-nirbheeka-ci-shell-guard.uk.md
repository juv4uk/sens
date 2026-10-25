# Nirbheeka · CI shell-quoting guard та естафета D1–D12+ · 25.10.2026

## Точна вершина

- Репозиторій: `juv4uk/sens`, гілка `main`.
- Цей хід: `fdbec8172ce2ff79ed87914821a7b9c9e5b9c044` — `CI: fail fast on semantic T5M runner shell syntax`.
- Зміна CI: `.github/workflows/ci.yml` запускає `bash -n scripts/prove-lisp-semantic-t5m.sh` після структурного перевіряльника shell-блоків і до тестів/збірки. Це рання перевірка синтаксису runner-а; вона не є доказом семантичного PASS.
- Передумова: `539318ba` перевів D9/F6 проби з аргументів із чутливим quoting на heredoc; пізніший `98214c2` виправив quoting у виразах SENS з апострофом у назві. Новий крок запобігає повторенню такого збою після дорогих фаз.
- У поточному `crates/sens-cli/src/bin/sens-math-t5m.rs` присутній тест `d12_t5m_rejects_rational_literals_but_preserves_sens_computed_ratios` (blob `add79f11f0fce05c4f4c992b3dab6216ee8b792a`).

## Межа доказів

- GitHub Combined Status для `fdbec8172ce2ff79ed87914821a7b9c9e5b9c044` повернув `statuses=[]`. Це не PASS.
- Доступний конектор не показав workflow runs для цього push SHA; локальне клонування не вдалося через недоступність DNS до github.com у поточному середовищі.
- Цей хід не виконав нативні SENS/Zig/T5M бінарники. Не оголошувати D12 новий тест, F6 producer→consumer чи загальний CI зеленими.
- Поточний `lib/lisp-fs.lisp` має blob `07bc8ef26ff2a3366d24ea64cb0d8e7112d03d14`. D9/F6 зміни канонізації і фізичні пари вимагають перевірки нативним runner-ом на одному SHA.

## Наступні дії

1. Отримати фактичний GitHub Actions run на exact SHA `fdbec8172ce2ff79ed87914821a7b9c9e5b9c044`. Перевірити новий ранній `bash -n` та зібрати першопричину найпершого червоного кроку.
2. На тому самому SHA виконати `cargo test -p sens-cli --test wsm_fs_f6_pipeline`, штатний source→Zig/T5M remint і повний `scripts/prove-lisp-semantic-t5m.sh`; зберегти фактичні D1/Type-результати й SHA джерел/фізичних пар.
3. Якщо F6 повертає `invalid-format`, звірити SENS `фс-формат-кореня?`, `фс-пакет-поле` та `F6_FORMAT_BRIDGE_D1`. Не послаблювати allowlist і не перетворювати довільні ключі на протокольні.
4. Після фізичного F6 доказу: переаудит D6 за Contract 12.0; довести прямий MAP; реалізувати справжній macro environment для D6:000110 MACROEXPAND-1 і D6:000111 MACROEXPAND з позитивними, негативними й lexical-shadowing свідками.

```text
D12_RATIONAL_BOUNDARY_TEST=IN_MAIN_NATIVE_NOT_VERIFIED
CI_BASH_SYNTAX_GUARD=IN_MAIN_NATIVE_NOT_VERIFIED
F6_PRODUCER_CONSUMER=NOT_VERIFIED
PHYSICAL_T5M_PARITY=NOT_VERIFIED
D6_MAP_DIRECT_CALL=NOT_VERIFIED
D6_MACROEXPAND_1=INCOMPLETE
D6_MACROEXPAND=INCOMPLETE
D1_D12_PLUS_FULL_FUNCTION_AUDIT=INCOMPLETE
RELEASE=NO-GO
```
