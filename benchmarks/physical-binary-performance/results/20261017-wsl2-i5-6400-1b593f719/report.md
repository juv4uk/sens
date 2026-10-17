# Фізична двійкова SENS — вимірювання часу й щільності

Commit: `1b593f719ad9d64a46363b22d918afac0ca0e94f`; runner CPU: Intel(R) Core(TM) i5-6400 CPU @ 2.70GHz

CLI SHA256: sens=`93f2204bd27356e35f35b741b454ccd775ffeab1786043bbd02dd88fe733c640`; sens-trit=`0dca437e562cd90584513d1fbccbf793aabe9ea3b0a921a561ebaba6658aac98`.
Codec SHA256: `ecbf923f240864374fbe06d553b5101c5d3574f8e58509628851118f2038fc10`; benchmark SHA256: `8ab815db9126db08f3e638074b3f1fc9803c24835bff6fb4b007081842f43bda`.

## Source → фізичне T5 кодування

| Джерело | Source bytes | T5 bytes | encode median, ms | encode p95, ms | Байтова тотожність |
|---|---:|---:|---:|---:|---|
| quote-legacy.sens#canonical-word-projection | 17 | 4 | 2.552 | 3.246 | PASS |
| two-forms.sens#canonical-word-projection | 70 | 14 | 2.741 | 4.625 | PASS |
| branch.sens#canonical-word-projection | 57 | 12 | 2.490 | 4.072 | PASS |
| pair-cons.sens#canonical-word-projection | 50 | 10 | 2.456 | 9.789 | PASS |
| pair-car-cdr.sens#canonical-word-projection | 56 | 11 | 2.546 | 3.545 | PASS |
| caar.sens#canonical-word-projection | 97 | 20 | 2.628 | 3.067 | PASS |
| eq-cond-select.sens#canonical-word-projection | 166 | 33 | 2.527 | 2.950 | PASS |
| eq-cond-skip.sens#canonical-word-projection | 166 | 33 | 2.344 | 4.357 | PASS |

Це процесне source→packed-T5 кодування, а не генерація нативного машинного коду.
До runtime вимірів допускається лише артефакт, байти якого точно збігаються з канонічним `.sens`.

| Програма | Шлях | Медіана, мс | p95, мс | Перший preflight, мс | I refs |
|---|---|---:|---:|---:|---:|
| quote-legacy.sens | sens-exec | 2.818 | 4.026 | 2.720 | — |
| quote-legacy.sens | sens-trit-eval | 2.825 | 5.207 | 2.564 | — |
| quote-legacy.sens | sens-trit-open | 2.310 | 4.783 | 1.986 | — |
| two-forms.sens | sens-exec | 3.089 | 7.186 | 3.379 | — |
| two-forms.sens | sens-trit-eval | 3.087 | 8.278 | 2.653 | — |
| two-forms.sens | sens-trit-open | 2.433 | 4.905 | 2.000 | — |
| branch.sens | sens-exec | 2.680 | 4.802 | 2.904 | — |
| branch.sens | sens-trit-eval | 2.822 | 5.949 | 3.356 | — |
| branch.sens | sens-trit-open | 2.245 | 3.176 | 2.459 | — |
| pair-cons.sens | sens-exec | 2.793 | 11.609 | 2.799 | — |
| pair-cons.sens | sens-trit-eval | 2.965 | 10.504 | 3.645 | — |
| pair-cons.sens | sens-trit-open | 2.466 | 13.094 | 2.225 | — |
| pair-car-cdr.sens | sens-exec | 2.755 | 4.260 | 2.663 | — |
| pair-car-cdr.sens | sens-trit-eval | 2.964 | 4.515 | 2.790 | — |
| pair-car-cdr.sens | sens-trit-open | 2.288 | 5.049 | 2.154 | — |
| caar.sens | sens-exec | 2.804 | 10.025 | 4.361 | — |
| caar.sens | sens-trit-eval | 3.001 | 9.487 | 3.462 | — |
| caar.sens | sens-trit-open | 2.390 | 5.121 | 37.181 | — |
| eq-cond-select.sens | sens-exec | 3.125 | 9.410 | 2.851 | — |
| eq-cond-select.sens | sens-trit-eval | 3.304 | 9.869 | 2.611 | — |
| eq-cond-select.sens | sens-trit-open | 2.574 | 9.177 | 2.620 | — |
| eq-cond-skip.sens | sens-exec | 3.339 | 9.138 | 2.908 | — |
| eq-cond-skip.sens | sens-trit-eval | 3.194 | 16.610 | 3.179 | — |
| eq-cond-skip.sens | sens-trit-open | 2.464 | 9.858 | 6.215 | — |

## Реальна щільність

| Файл | Фізичні байти | Видимі ASCII-байти | Видимі / фізичні |
|---|---:|---:|---:|
| quote-legacy.sens | 4 | 17 | 4.250× |
| two-forms.sens | 14 | 70 | 5.000× |
| branch.sens | 12 | 57 | 4.750× |
| pair-cons.sens | 10 | 50 | 5.000× |
| pair-car-cdr.sens | 11 | 56 | 5.091× |
| caar.sens | 20 | 97 | 4.850× |
| eq-cond-select.sens | 33 | 166 | 5.030× |
| eq-cond-skip.sens | 33 | 166 | 5.030× |

Обидві CLI-дороги дали однакові байти результату. Це лише parity
механізмів; семантичні закони встановлюють Lisp-оракули.
Кожна вибірка запускає **новий процес**. p95 — nearest-rank;
міжмашинні порівняння без однакового обладнання невалідні.
Час відлічується навколо subprocess і включає startup, I/O та stdout.
Перший preflight замір перед прогрівами; холодний OS page cache НЕ доведений.
Видимі байти рахуються з канонічним кінцевим LF, перевіреним Python T5-кодеком.
Ширина кожного слова збережена в typed SHA256; це транспортний доказ.
