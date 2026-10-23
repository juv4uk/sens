# T5M / T33 / D12: відтворюваний фізичний мікробенчмарк

Статус додавання: **IMPLEMENTED / UNVERIFIED**. У середовищі автора немає
Zig; нових нативних p50/p95 не отримано. Це не звіт швидкості SENS evaluator.
T33R: **NOT_IMPLEMENTED** (на момент аудиту немає окремого native codec).

## Запуск і межа

За наявного pinned Guix: `./guix/run dev -- zig test -lc research/zig-codecs/codec_compare_bench.zig`.
Ручний existing workflow `.github/workflows/zig-ladder-tools.yml` установлює
Zig 0.16.0, тестує й компілює цей файл `-O ReleaseFast -lc`, зберігає
`codec_compare.log` у своєму artifact. Нових автоматичних workflow немає.

Лог містить source commit, Zig version, uname/lscpu, SHA-256 вихідних кодів
і executable, exact carrier lengths, roundtrip, 21 сирий batch на випадок
(300 повторів; один прогрітий batch для кожної операції). p50 = відсортований
елемент 11/21, p95 = 20/21 (nearest rank); числа — ns/op за batch averages,
**не p95 latency окремого запиту**, не CI/confidence interval.
Кодекові API alloc/free включено; startup, I/O й evaluator виключено.
Encode/decode порядок чергується; D12 codec порядок ротовано за парністю
count. Один hosted процес не усуває noise/drift; загальні speedup мови не заявляються.

T5M/T33 повертають exact-width bit strings; D12 повертає u16 words і потребує
**зовнішніх width=12 та word_count**. Тому D12 — payload_bytes, а
frame_bytes=NOT_DEFINED. Різні API/алокації — властивість цих реалізацій,
не ізольована оцінка bit-packing циклу. Для mixed-width корпусів D12 не запускається.
Загальний transport не надає семантичного допуску для довільних ширин.

## Точні fixtures

- `pattern-10-100-01`: `[(2,"10"),(3,"100"),(2,"01")]` повторено N=1,16,128,1024;
  слова не проголошуються валідною програмою. Trit count = 10N−1.
- `width-boundary-zero`: одне слово з W нулів;
  W=1,4,5,32,33,34,127,128,231. Повні блоки 33, T5M tail, ULEB boundary.
- `d12-affine-v1`: N=1,2,3,10,11,127,128,129,1024; нуль-базований
  i=0..N−1; raw[i]=(73i+137 floor(i/2)) mod 4096. Слово — рівно 12 бітів
  MSB-first, включно зі старшими нулями. Trit count = 13N−1.
- `d12-extremes`: точні слова `000000000000 111111111111 100000000000 000000000001 011111111111`.

Ці визначення разом із pinned source SHA — exact corpus, не випадкова вибірка.
SHA в workflow — provenance поза транспортом; не умова мовної identity.

## Аналітичні sizes, НЕ нативне вимірювання

Для T тритів: T5M=ceil(T/5); T33=2+ULEB_length(T)+6 floor(T/33)+ceil((T mod 33)/5).
Для N D12 слів payload=ceil(12N/8). Формули прочитано з реалізацій;
нижче **не результат запуску** нового harness.

| D12 слів | T5M carrier B | T33 framed B | D12 payload B, без metadata |
|---:|---:|---:|---:|
| 1 | 3 | 6 | 2 |
| 2 | 5 | 8 | 3 |
| 3 | 8 | 10 | 5 |
| 10 | 26 | 28 | 15 |
| 11 | 29 | 30 | 17 |
| 127 | 330 | 304 | 191 |
| 128 | 333 | 307 | 192 |
| 129 | 336 | 310 | 194 |
| 1024 | 2663 | 2425 | 1536 |

У власному Zig test exact two-word fixture `000000000000 000001001001`
вимагає 5/8/3 B і повного width/bits roundtrip; D12 odd-tail mutant
`00 01` з count=1 мусить дати `NonCanonicalTail`.
До нативного проходження тесту це очікування, не PASS.
