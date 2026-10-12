# Відновлені унікальні benchmark-джерела — 12.10.2026

Цей каталог зберігає байт-точні файли з історичних гілок бенчмарків, яких не було знайдено за початковим шляхом у поточному `main`.

**Це source archive, не active benchmark suite.** Усі файли мають суфікс `.source.txt`, тому вони не є активними GitHub Actions workflow, Lisp-модулями, тестами чи production-кодом. Оригінальні refs використовували застарілі назви `my-lisp` / `my-lisp-cli` і API; запуск без адаптації заборонений.

Точні origin ref, шлях, Git blob SHA й archive path описані в `manifest.json`. SHA перевіряється на оригінальному ref перед копіюванням. Збереження джерела не доводить, що benchmark досі компілюється, має правильний oracle або дає чинний performance result.

## Групи
- `encoder-same-input`: парне дослідження фізичних T5/F3/F4 носіїв.
- `utf8-fused`: історична спроба fused UTF-8 decoder і її profiler/witness.
- `readfile-production`: історична композиція Lisp `read-file` та окремий profiler.
- `readfile-legacy`: попередня версія #74 read-file harness до переходу на canonical binary source; три refs мають однакові вихідні blob SHA й архівуються один раз.

Не переносити старі файли поверх актуальних `lib/utf8.lisp`, `lib/fs.lisp`, benchmark registry або workflow. Для активного повернення потрібні окрема адаптація на main, exact byte/parity checks, незалежний correctness oracle, raw samples і green CI.
