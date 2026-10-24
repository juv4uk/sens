# SENS WASM

WASM-прив'язка тримає сталу `Session` між викликами `evaluate()` і надає browser/embedder-рівню перемикання програмних поверхонь без зміни семантичного контракту мови.

## Surface API

```javascript
wasm.set_surface("ук");
wasm.set_surface("ukr");
wasm.set_surface("en");
wasm.set_surface("sa");
wasm.set_surface("core");

wasm.current_surface();
```

`set_surface()` змінює лише проміжний surface-frame. Користувацький frame лишається тим самим, тому визначення й closures поточної сесії не відкидаються й не replay-яться.

Схема середовища:

```text
base
  ↓
surface
  ↓
user
```

Повна користувацька документація: [`docs/repl-surfaces.md`](../../docs/repl-surfaces.md).
