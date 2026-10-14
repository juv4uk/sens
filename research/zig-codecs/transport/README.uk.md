# Zig — freestanding-механізм конверта SENS

**Статус:** транспортний дослідний механізм, НЕ новий E1/E2/E3 wire-стандарт, НЕ production cutover. Zig **0.16.0**.

Закон конверта належить SENS. Код `fields.zig` НЕ призначає нормативних значень version/profile, не вигадує ширин полів або правил EOF, не оголошує будь-які SENS-слова виконуваними. Наявні конверти E1/E2/E3 і T5/F3C/F3M залишаються різними сімействами.

У Zig реалізовано безалокаторні механізми: MSB-first двійкові метадані з явними width/meaningful-bit length, канонічний tail без прихованих бітів, перевірка карти блоків за явним розміром payload, IEEE CRC32 фізичних байтів (той самий механізм, що в Rust E1/E2; CRC НЕ є MAC). Немає залежності від libc, файлового I/O, мережі, апаратного драйвера чи heap у виробничих функціях; `std.testing` лише в самотестах.

**Запуск механічних свідків:**

    zig version  # 0.16.0
    zig test research/zig-codecs/transport/fields.zig
    zig test research/zig-codecs/tests.zig

Є позитивні приклади ширин із провідними нулями, CRC golden; негативні one-bit tail та CRC мутації, обрізання/подовження повідомлення, надширокого поля, проміжку та перекриття фізичних блоків.

**Наступні ворота:** вибрати затверджений E1/E2/E3 binary layout як незалежне джерело widths/версій/профілів/CRC coverage; виконати Zig↔Rust byte-exact паритет на фізичних файлах та негативних мутантах; перевірити `-target xtensa-freestanding`, linker/ABI та hardware ESP32-S3; отримати нативні двійкові SENS semantic receipts; окреме рішення власника перед production перемиканням.

Доказові питання: [#2189](https://github.com/juv4uk/sens/issues/2189) (EOF), [#5766](https://github.com/juv4uk/sens/issues/5766) (Zig codecs), [#5770](https://github.com/juv4uk/sens/issues/5770) (parity), [#5771](https://github.com/juv4uk/sens/issues/5771) (bench).