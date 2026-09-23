# FASL snapshot — дизайн-чернетка (OPT item #4)

**Статус:** DRAFT · 2026-08-24 · Vyasa
**Проблема:** `Session::default()` і кожен CLI-запуск парсять `lib/core4.lisp`
(644 рядки, 49 def-ів) через `include_str!` (main.rs:76). Fresh-session
бенчмарки показують 24–89µs/op з домінуючим parse+load. Для one-shot батчів
(WSM-24: тисячі процесів-яєць) це ×N системної втрати.

## Мета
Кешувати **вихід парсера** (Vec<Expr>) у бінарний артефакт; бінарник читає
байти замість текстового парсингу. Жодних змін семантики/eval — тільки
транспорт між `parse()` і `eval_parsed_expressions`.

## Формат (чернетка v0)
```
magic   "MYF1"            (4B)
u32     format_version    (1)
u32     contract_major/minor  (звірка з language-contract.lisp)
32B     sha256(concatenated sources)   -- identity + invalidation
repeated Expr records:
  u8 tag (Number/Rational/String/Symbol/List/Pair/Nil...)
  Number:   8B f64 bits + u8 exactness
  Rational: u32 num_len + num_bytes + u32 den_len + den_bytes (decimal strings, як from_literal)
  String/Symbol: u32 len + bytes
  List: u32 count + records
  Pair: record head + record tail
```
Детерміновано → sha256 снапшота = частина ідентичності артефакту.

## Інвалідація (найважливіше)
Loader ПЕРЕВІРЯЄ sha256 джерел проти вбудованого; mismatch → **fallback на
звичайний parse** (ніколи не мовчки використовувати застарілий снапшот).
Fallback логується. Це робить механізм безпечним при будь-якому дрейфі.

## Інтеграція
1. `scripts/gen-fasl.sh`: читає lib/*.lisp → пише `lib/core4.lisp.fasl` (+sha)
2. build.rs АБО include_bytes! фікс-артефакту в my-lisp-cli
3. CLI прапорець `--no-fasl` — завжди доступний чистий parse-шлях (debuggability)

## Очікуваний ефект
Cold-session бенчмарк-кейси (arithmetic/closures/lists/recursion — усі
платять core4.lisp parse щоразу) мають впасти пропорційно частці парсинга;
one-shot батчі — головний виграш. Замір: той самий harness, A/B з/без fasl.

## Не-цілі
Без байткоду, без JIT, без змін eval. Це кеш parse-виходу — нічого більше.

## Ризики
- Дрейф формату між версіями компілятора → гаситься version+sha перевіркою
- Розмір бінарника +~50–100KB (несуттєво)
- Хибне відчуття «ще один формат» → формат приватний для бінарника, не контрактний

## ⚠️ Регенерація після зміни lib/core4.lisp

Якщо хтось редагує `lib/core4.lisp` — FASL-снапшот (`lib/core4.lisp.fasl`)
автоматично стає невалідним (sha256 mismatch). Це БЕЗПЕЧНО: CLI
мовчки падає на text-parse fallback. Але перформанс-виграш втрачається.

Перегенерувати:
```bash
cargo run --release -p my-lisp-cli --bin gen-fasl -- lib/core4.lisp lib/core4.lisp.fasl
git add lib/core4.lisp.fasl && git commit -m "chore(fasl): regenerate after core.lisp change"
```
