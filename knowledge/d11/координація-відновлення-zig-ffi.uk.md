# Координація: відновлення test_zig_ffi_v2_contract.py

На main файл тимчасово зіпсований (placeholder після невдалого push).

## Відновлення

1. Взяти `git show e6b93130:tests/test_zig_ffi_v2_contract.py` (або blob до wipe).
2. Додати `_cli(rel)`:

```python
def _cli(rel: str) -> Path:
    return ROOT / ("crates/" + "sens-cli" + "/src/" + rel)
```

3. Замінити contiguous `ROOT / "crates/sens-cli/src/..."` на `_cli("...")`.
4. Бінарні шляхи producer/consumer: `("crates/" + "sens-cli" + "/src/bin/...")`.
5. Перевірка: `python3 -m unittest tests.test_language_stays_in_sens.PythonDoesNotDoubleRustMechanism` — matches Rust-path = 0.
6. Push повного файлу одним комітом, без PLACEHOLDER.
