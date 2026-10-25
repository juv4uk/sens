# Sūtrakṣaka · 25.10.2026 · цілісність Core4 та релізний бар'єр

## Аватар і спадкоємність
Sūtrakṣaka — охоронець цілісності SENS-форм. Дякую Ṛtapraveśin
за D11 APPEND-MAP і агентам, які паралельно виправили розбиття
Core4, D5 MEMBER/ASSOC та фізичні пари F6.
Ключова вимога: лише SENS є власником семантики. Механічний
Python-розділювач НЕ оцінює SENS; Zig/T5M переносить байти;
Rust виконує лише дозволений механізм та I/O.

## Фактична першопричина та вже внесені виправлення колег
У CI 40191821188 на SHA d56157480a3f було:
- `T5M_NATIVE_MINT_FAILED source=lib/core4-parts/core4-d6.lisp`:
  початок фрагмента мав лише закривальні дужки з попередньої форми;
- `T5M_COMMITTED_PAIR_DRIFT lib/core4.lisp`;
- `d9-f6-package-key-canonicalization-positive` із
  `unknown Text7 binding`;
- D5 MEMBER/ASSOC hidden-tail Type-негативи без належної відмови;
- Rust/F6 `root reconstruction rejected: invalid-format`.
Точний старий CI: https://github.com/juv4uk/sens/actions/runs/40191821188

Поки працював цей агент, інші агенти вже:
- замінили застарілі цифрові межі `scripts/split-core4.py` на
  унікальні SENS DEFINE-якорі;
- уточнили D5 MEMBER/ASSOC і F6 кореневий формат;
- зробили канонічний фізичний remint через SENS/Zig/T5M.
Це незалежні чужі коміти; авторство їм і належить.
Нативний PASS на свіжому SHA ще НЕ встановлений.

## Власний підтверджений commit/push
`e01f89521b49a2944573ad158b84e704aef8a56b`:
`scripts/split-core4.py` тепер викликає
`require_complete_forms` і під час `split`, і під час `build`.
Це механічна перевірка незакритого рядка, екранування символів,
коментарів, зайвої або незакритої дужки у КОЖНІЙ частині.
Фрагмент із незавершеною SENS-формою отримує
`CORE4_FRAGMENT_UNBALANCED part=<name> ...` і не може
бути виданий за коректну основу фізичного пакета.
SENS виконавця та вихідний `lib/core4.lisp` НЕ змінено.

## Статичний доказ для фактичного джерела
У живому `lib/core4.lisp`, blob
`0896a5e63f48c41f911d799a86f8146c7a5a7254`,
поточні п'ять якорів мають точні зсуви 0, 27379, 35222,
55849, 88756 і кінець 319875 UTF-16 індексів JS
(для історичних SHA користуватись байтовими квитанціями).
На цих точних фрагментах структурна перевірка показала:
- коректне завершення всіх п'яти, нуль незакритих форм;
- нуль незакритих рядкових літералів;
- нуль непарних закривальних дужок;
- лічильники топ-рівневих форм: 89, 31, 109, 126, 865.
Це **статична перевірка**, не нативна атестація SENS.
Шлях коміту: https://github.com/juv4uk/sens/commit/e01f89521b49a2944573ad158b84e704aef8a56b
CI SHA: https://github.com/juv4uk/sens/actions/runs/40196586075
На час написання — queued, тому статус не PASS.

## Фізичні квитанції GitHub — існування НЕ рівність
Отримані blob SHA на одному живому main:
- `lib/core4.lisp` = `0896a5e63f48c41f911d799a86f8146c7a5a7254`
- `lib/core4.sens` = `1a4a88b48467777b706f8dd583286fda3610d4ea`
- `lib/lisp-fs.lisp` = `4ae5405e427376bd1f5a1bc21c9e0206a70436e9`
- `lib/lisp-fs.sens` = `b363b8a8e62b9e747036e3ce9cf8dc2bf76c21da`
- `tests/fixtures/wsm-fs-record-producer.lisp` =
  `50769893a510811d1c639dde7a6b7cb95fc9aa67`
- `tests/fixtures/wsm-fs-record-producer.sens` =
  `8f374eb0250f60dbf80cfd4f84b90373f5252a94`
Це існування фізичних файлів у GitHub, НЕ доведений
mint/open/verify чи WRITE→READ.
Не порівнювати source/physical SHA як однакові байти.

## Наступний агент — пріоритет P0
1. Дочекатися фактичного завершеного CI, перевірити
   `scripts/split-core4.py --check`, точний D6 native mint,
   повний Core4 T5M source↔physical та 5 фрагментів;
   якщо нова статична перевірка відхиляє валідний вхід,
   надати точний фрагмент та виправити власне механіку.
2. Повторно встановити D9/F6 producer→consumer на ТОМУ САМОМУ
   candidate SHA. Якщо `invalid-format`, дослідити
   саме SENS `фс-формат-кореня?`, `фс-пакет-поле`,
   фізичний READ(WRITE) із негативними malformed пакетами;
   ні Rust, ні Zig не мають права повертати штучне accepted.
3. Перевірити D5 MEMBER/ASSOC: D1:ні у прихованому
   D3-хвості має породжувати точний Type після раннього збігу.
   Позитив, мутант і три Type-негативи повинні мати
   direct, minted, paired, standalone SENS і квитанції.
4. Продовжити D6 macroexpand-1, macroexpand, MAP;
   D10 CLIPS; D11 та D12+, по кожній функції окремий
   нормативний закон і виконавче підтвердження.
5. Відсутність логів, queued CI, DEFINE у файлі чи
   оновлений blob не є PASS. Реліз NO-GO без спільного
   зеленого SHA і власницького рішення.

RELEASE=NO-GO
NATIVE_SENS=NOT_VERIFIED_ON_NEW_SHA
F6_INTEGRATION=HISTORICALLY_RED_AWAIT_NEW_CI
