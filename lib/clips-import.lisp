; Імпортер історичних систем символьного штучного інтелекту.
; Перший підтриманий формат — CLIPS, створений у NASA Johnson Space Center.
; Правила прямого виведення розвиваються окремо в lib/forward.lisp.
;
; Зовнішні S-вирази читаються як дані, а не виконуються як програми СЕНС.
; Мова не потребує окремого токенізатора CLIPS чи нового примітива Rust:
; гомоіконічність дає змогу розбирати структуру списків засобами Lisp.
; Наприклад, чужа форма (defrule foo (bar ?x) => (assert (baz ?x)))
; містить лише символи зовнішньої граматики, а не викличні голови СЕНС.
;
; Перший етап імпорту: оголошення CLIPS deffacts без змінних.
; Форми (deffacts name (fact1 ...) (fact2 ...) ...) стають окремими
; клаузами (head . body), які очікує мовна система модулів.
; Підтримка defrule, перетворення змінних ?x на (var x) та виконання
; правил не випливають з одного лише читання форми.
;
; Наступний етап: шаблони CLIPS deftemplate з іменованими слотами.
; Позиційний факт (planet earth) не має іменованих слотів.
; Шаблон (deftemplate reading (slot sensor) (slot value)) задає порядок
; sensor, value. Тому (reading (value 98) (sensor probe1))
; перетворюється на позиційний (reading probe1 98), незалежно
; від порядку запису слотів у вихідному факті.
;
; Імпортер спочатку одноразово проходить усі форми та складає
; звичайний список (назва . (слот1 слот2 ...)). Далі зіставлення
; фактів, умов і висновків користується цим списком без змінюваного
; глобального реєстру. Терми без відомого імені шаблону
; проходять без змін. Імена зовнішніх форм залишено точними
; протокольними даними, а не латинськими викликами СЕНС.
;
(визначити кліпс-визначити-шаблон-форма?
  (функція (форма)
    (за-умовою
      ((атом? форма) ні)
      ((хибне? (атом? (перше форма))) ні)
      ((тотожне? (перше форма) (як-є deftemplate)) так)
      (так ні))))

; Real CLIPS files namespace their deftemplate/deffacts names with a
; `defmodule` prefix, e.g. `QUESTIONS::question`. `wine-external.clp`
; (fetched from CLIPS's own examples) declares `(deftemplate QUESTIONS::question ...)`
; but then asserts plain `(question ...)` facts inside `deffacts` — CLIPS
; resolves the bare name against whichever module is current, but this
; importer has no notion of modules at all. Stripping every name down to
; whatever follows the last `::` (or the whole name, if there is none)
; before it ever reaches the template alist lets bare and qualified names
; match each other, without needing to model `defmodule` for real.
; Реальні CLIPS-файли простороюють імена deftemplate/deffacts префіксом
; `defmodule`, напр. `QUESTIONS::question`. `wine-external.clp` (зі
; справжніх прикладів CLIPS) оголошує `(deftemplate QUESTIONS::question ...)`,
; але потім у `deffacts` асертує прості факти `(question ...)` — CLIPS сам
; резолвить голе ім'я відносно поточного модуля, а цей імпортер модулів
; узагалі не знає. Обрізання кожного імені до частини після останнього
; `::` (або всього імені, якщо `::` немає) ще до потрапляння в реєстр
; шаблонів дозволяє голим і кваліфікованим іменам збігатися одне з одним,
; без реальної підтримки `defmodule`.
; Echte CLIPS-Dateien versehen deftemplate/deffacts-Namen mit einem
; `defmodule`-Präfix, z.B. `QUESTIONS::question`. `wine-external.clp` (aus
; den echten CLIPS-Beispielen) deklariert `(deftemplate QUESTIONS::question ...)`,
; asserted dann aber schlichte `(question ...)`-Fakten in `deffacts` — CLIPS
; löst den nackten Namen selbst gegen das aktuelle Modul auf, dieser
; Importer kennt Module überhaupt nicht. Jeden Namen schon vor der
; Aufnahme in die Vorlagen-Registry auf den Teil nach dem letzten `::`
; zu kürzen (oder den ganzen Namen, falls kein `::` vorkommt) lässt nackte
; und qualifizierte Namen einander finden, ohne `defmodule` wirklich
; abzubilden.
(визначити кліпс-рядок-порожній? (функція (рядок) (тотожне? рядок "")))

; This is a D1 predicate, not a partial search returning NIL on failure.
; D3 COND can inspect only the exact one-bit results; empty/short strings,
; mismatched first character and mismatched second character are all D1:NO.
(визначити кліпс-рядок-починається-з-подвійної-двокрапки?
  (функція (рядок)
    (за-умовою
      ((кліпс-рядок-порожній? рядок) ні)
      ((кліпс-рядок-порожній? (рядок-решта рядок)) ні)
      ((тотожне? (рядок-перший рядок) ":") (тотожне? (рядок-перший (рядок-решта рядок)) ":"))
      (так ні))))

(визначити кліпс-рядок-після-останньої-подвійної-двокрапки
  (функція (рядок)
    (за-умовою
      ((кліпс-рядок-порожній? рядок) (як-є ()))
      ((кліпс-рядок-починається-з-подвійної-двокрапки? рядок)
       ((функція (залишок)
          (за-умовою
            ((тотожне? залишок (як-є ())) (рядок-решта (рядок-решта рядок)))
            (так залишок)))
        (кліпс-рядок-після-останньої-подвійної-двокрапки (рядок-решта (рядок-решта рядок)))))
      (так (кліпс-рядок-після-останньої-подвійної-двокрапки (рядок-решта рядок))))))

(визначити прибрати-префікс-модуля-кліпс
  (функція (позначення)
    (за-умовою
      ((символ? позначення)
       ((функція (залишок)
          (за-умовою
            ((тотожне? залишок (як-є ())) позначення)
            (так (текст-у-символ залишок))))
        (кліпс-рядок-після-останньої-подвійної-двокрапки (символ-у-текст позначення))))
      (так позначення))))

(визначити кліпс-визначити-шаблон-ім'я (функція (форма) (прибрати-префікс-модуля-кліпс (друге форма))))

(визначити кліпс-слот-ім'я (функція (форма-слота) (друге форма-слота)))

(визначити кліпс-слот-імена
  (функція (форми-слотів)
    (за-умовою
      
      ((атом? форми-слотів)  (як-є ()))
      (так (сполучити (кліпс-слот-ім'я (перше форми-слотів)) (кліпс-слот-імена (решта форми-слотів)))))))

(визначити кліпс-визначити-шаблон-слоти
  (функція (форма)
    (кліпс-слот-імена (решта-решти форма))))

(визначити кліпс-шаблони-з-форми
  (функція (форми)
    (за-умовою
      
      ((атом? форми)  (як-є ()))
      ((кліпс-визначити-шаблон-форма? (перше форми))
       (сполучити (сполучити (кліпс-визначити-шаблон-ім'я (перше форми)) (кліпс-визначити-шаблон-слоти (перше форми)))
             (кліпс-шаблони-з-форми (решта форми))))
      (так (кліпс-шаблони-з-форми (решта форми))))))

; Реєстр шаблонів є списком пар (атомарна-назва . порядок-слотів).
; Пошук визначено структурно, без неявного допуску D5 ASSOC або
; D8 EQUAL як викличних операцій. Порожні й некоректні записи
; повертають порожні дані (), а не предикатну хибу D1.
(визначити кліпс-шаблон-слот-порядок
  (функція (назва шаблони)
    (за-умовою
      ((хибне? (атом? назва)) (як-є ()))
      ((атом? шаблони) (як-є ()))
      ((атом? (перше шаблони))
       (кліпс-шаблон-слот-порядок назва (решта шаблони)))
      ((хибне? (атом? (перше (перше шаблони))))
       (кліпс-шаблон-слот-порядок назва (решта шаблони)))
      ((тотожне? назва (перше (перше шаблони))) (решта (перше шаблони)))
      (так (кліпс-шаблон-слот-порядок назва (решта шаблони))))))

; Умова CLIPS може вказувати мультислот без значення.
; Зокрема (precursors) у правилі ask-a-question означає,
; що вміст слота довільний, навіть порожній.
; Якщо форма слота не містить другого елемента,
; повертаємо порожні дані — тобто відсутність обмеження.
; Не викликаємо селектор другого елемента над неповною формою.
; Імена CLIPS у цих прикладах належать зовнішньому протоколу.
(визначити кліпс-значення-слота
  (функція (форма-слота)
    (за-умовою
      
      ((атом? (решта форма-слота))  (як-є ()))
      (так (друге форма-слота)))))

; Точний D3 пошук атомарної назви CLIPS-слота.
; Коректний слот = (назва значення). У разі складеної назви
; пропускаємо запис; голий атом замість слота теж пропускаємо.
; Не можна відкидати кожний непорожній список: порівняння
; тоді недосяжне. Рядки в кліпс-символ-починається-з-питальника? і далі D8 EQUAL.

(визначити знайти-значення-слота-кліпс
  (функція (назва-слота форми-слотів)
    (за-умовою
      
      ((атом? форми-слотів)  (як-є ()))
      ((атом? (перше форми-слотів))  (знайти-значення-слота-кліпс назва-слота (решта форми-слотів)))
      ((хибне? (атом? (перше (перше форми-слотів)))) (знайти-значення-слота-кліпс назва-слота (решта форми-слотів)))
      ((тотожне? назва-слота (перше (перше форми-слотів))) (кліпс-значення-слота (перше форми-слотів)))
      (так (знайти-значення-слота-кліпс назва-слота (решта форми-слотів))))))

(визначити позиційні-аргументи-кліпс
  (функція (порядок-слотів форми-слотів)
    (за-умовою
      
      ((атом? порядок-слотів)  (як-є ()))
      (так (сполучити (знайти-значення-слота-кліпс (перше порядок-слотів) форми-слотів)
                (позиційні-аргументи-кліпс (решта порядок-слотів) форми-слотів))))))

; Крок 13: рекурсивне перетворення іменованих слотів охоплює
; не тільки заперечення not, а й вкладені умови or, and,
; а також квантори exists і forall.
; Раніше приклад (or (cat (name ?x)) (dog (name ?x)))
; не змінювався, тому не міг зіставитися з позиційним
; фактом (cat tom) і правило помилково не давало висновків.
; Тепер кожну вкладену умову обходимо за тим самим законом.
; Зовнішнє not перетворюємо на протокольний терм not?,
; а не виконуємо як виклик СЕНС у цьому імпортері.
(визначити кліпс-перетворити-шаблон
  (функція (терм шаблони)
    (за-умовою
      
      ((атом? терм)  терм)
      ((хибне? (атом? (перше терм))) (за-умовою
         ((тотожне? (перше терм) (як-є not)) (список (як-є not?) (кліпс-перетворити-шаблон (друге терм) шаблони)))
         ((тотожне? (перше терм) (як-є or)) (сполучити (як-є or) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є and)) (сполучити (як-є and) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є exists)) (сполучити (як-є exists) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є forall)) (сполучити (як-є forall) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         (так ((функція (порядок-слотів)
              (за-умовою
                
                ((атом? порядок-слотів)  терм)
                (так (сполучити (перше терм) (позиційні-аргументи-кліпс порядок-слотів (решта терм)))))) (кліпс-шаблон-слот-порядок (прибрати-префікс-модуля-кліпс (перше терм)) шаблони)))))
      ((атом? (перше терм))  (за-умовою
         ((тотожне? (перше терм) (як-є not)) (список (як-є not?) (кліпс-перетворити-шаблон (друге терм) шаблони)))
         ((тотожне? (перше терм) (як-є or)) (сполучити (як-є or) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є and)) (сполучити (як-є and) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є exists)) (сполучити (як-є exists) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є forall)) (сполучити (як-є forall) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         (так ((функція (порядок-слотів)
              (за-умовою
                
                ((атом? порядок-слотів)  терм)
                (так (сполучити (перше терм) (позиційні-аргументи-кліпс порядок-слотів (решта терм)))))) (кліпс-шаблон-слот-порядок (прибрати-префікс-модуля-кліпс (перше терм)) шаблони)))))
      (так терм))))

(визначити кліпс-перетворити-шаблон-список
  (функція (терми шаблони)
    (за-умовою
      
      ((атом? терми)  (як-є ()))
      (так (сполучити (кліпс-перетворити-шаблон (перше терми) шаблони)
                (кліпс-перетворити-шаблон-список (решта терми) шаблони))))))

(визначити кліпс-факт-клауза
  (функція (факт) (список факт)))

; `(cons ... (clips-facts->clauses ...))` is not a tail call — for a real
; CLIPS file with a big `deffacts` block (`animal-external.clp`'s own
; knowledge base is 128 facts in one block) the Rust call stack grew one
; frame per fact and overflowed. `-onto` accumulator + `reverse`, the same
; stack-safe shape `lib/core.lisp`'s own `map`/`filter` use, keeps every
; recursive call here in tail position.
; `(cons ... (clips-facts->clauses ...))` — не хвостовий виклик: на
; справжньому CLIPS-файлі з великим блоком `deffacts` (`animal-external.clp`'s
; власна база знань — 128 фактів в одному блоці) стек Rust ріс на один
; фрейм на факт і переповнювався. Акумулятор `-onto` + `reverse`, та сама
; стек-безпечна форма, яку використовують власні `map`/`filter` з
; `lib/core.lisp`, тримає кожен рекурсивний виклик тут у хвостовій позиції.
; `(cons ... (clips-facts->clauses ...))` ist kein Tail-Call — bei einer
; echten CLIPS-Datei mit einem großen `deffacts`-Block (`animal-external.clp`s
; eigene Wissensbasis hat 128 Fakten in einem Block) wuchs der Rust-Stack
; um einen Frame pro Fakt und lief über. Akkumulator `-onto` + `reverse`,
; dieselbe stack-sichere Form, die `lib/core.lisp`s eigene `map`/`filter`
; verwenden, hält jeden rekursiven Aufruf hier in Tail-Position.
(визначити кліпс-факти-у-клаузи-дописати
  (функція (факти шаблони накопичені)
    (за-умовою
      ((атом? факти) (зворот накопичені))
      (так (кліпс-факти-у-клаузи-дописати
           (решта факти) шаблони
           (сполучити (кліпс-факт-клауза (кліпс-перетворити-шаблон (перше факти) шаблони)) накопичені))))))

(визначити кліпс-факти-клаузи
  (функція (факти шаблони)
    (кліпс-факти-у-клаузи-дописати факти шаблони (як-є ()))))

; `(cddr form)` drops `deffacts` and the deffacts block's own name,
; leaving just the fact list.
(визначити кліпс-визначити-факти-клаузи
  (функція (форма шаблони)
    (кліпс-факти-клаузи (решта-решти форма) шаблони)))

; Крок 2: у CLIPS змінна має вигляд ?x, але читач Lisp
; розглядає її як звичайний атомарний символ.
; Для побудови логічного терма (var x) відкидаємо лише
; початковий знак питання, зберігаючи вихідне ім'я.
; Однакові ?x у межах правила повинні посилатися
; на ту саму логічну змінну.
; Застосовуємо перетворення символу на текст і назад,
; не додаючи прихованих механізмів виконавця.
;
; Аргумент факту може бути числом, наприклад (temperature 98).
; Тому перед текстовою операцією обов'язково перевіряємо,
; що терм справді є символом. Для пар та інших атомів
; повертаємо точну хибу D1, без істинності хоста.
(визначити кліпс-змінна?
  (функція (терм)
    (за-умовою
      ((атом? терм)
       (за-умовою
         ((символ? терм) (кліпс-символ-починається-з-питальника? терм))
         (так ні)))
      (так ні))))

; Both projections are atoms, so admitted D3 EQ suffices;
; D8 EQUAL is neither needed nor implicitly admitted here.
(визначити кліпс-символ-починається-з-питальника?
  (функція (символ)
    (тотожне? (рядок-перший (символ-у-текст символ)) (рядок-перший "?_"))))

(визначити кліпс-змінна-терм
  (функція (символ)
    (список (як-є var) (текст-у-символ (рядок-решта (символ-у-текст символ))))))

; Walks an arbitrary CLIPS term, replacing every `?x`-shaped symbol with
; `(var x)` and leaving everything else untouched.
(визначити кліпс-перетворити-змінні
  (функція (терм)
    (за-умовою
      ((кліпс-змінна? терм) (кліпс-змінна-терм терм))
      
      ((атом? терм)  терм)
      (так (сполучити (кліпс-перетворити-змінні (перше терм)) (кліпс-перетворити-змінні (решта терм)))))))

; Splits a defrule's body at `=>` into (conditions . conclusion-forms).
; Guards the `=>`-check with `(atom (car body))` first: a condition like
; `(planet ?x)` is itself a compound list, and `eq` errors on non-atom
; arguments instead of just correctly answering "not the `=>` marker".
(визначити розділити-правило-кліпс
  (функція (тіло)
    (за-умовою
      ((атом? тіло) (список (як-є ()) (як-є ())))
      ((атом? (перше тіло))
       (за-умовою
         ((тотожне? (перше тіло) (як-є =>)) (список (як-є ()) (решта тіло)))
         (так ((функція (решта-форм)
              (список (сполучити (перше тіло) (перше решта-форм)) (друге решта-форм)))
              (розділити-правило-кліпс (решта тіло))))))
      (так ((функція (решта-форм)
           (список (сполучити (перше тіло) (перше решта-форм)) (друге решта-форм)))
           (розділити-правило-кліпс (решта тіло)))))))

; Крок 3: у правій частині правила CLIPS може бути кілька assert.
; Кожне твердження утворює окрему клаузу з тим самим переліком умов:
; це відповідає спільному спрацьовуванню правила.
; Тут не вигадуємо семантику для інших дій CLIPS.
; Непідтримувані retract і modify не перетворюємо довільно.

(визначити твердження-кліпс?
  (функція (форма)
    (за-умовою
      ((атом? форма) ні)
      ((атом? (перше форма)) (тотожне? (перше форма) (як-є assert)))
      (так ні))))

; Крок 9: службове виведення printout поряд із assert не
; скасовує твердження, яке можна імпортувати.
; Приклад: (defrule mass-rule (planet ?x) =>
;           (printout t "found planet " ?x crlf)
;           (assert (has-mass ?x))).
; Виведення повідомлення не має окремого наслідку в базі фактів,
; але assert продовжує діяти.
; Дії retract та modify вимагають адрес CLIPS-фактів;
; структурна база СЕНС не повинна вдавати, що має ці адреси.

(визначити виведення-кліпс?
  (функція (форма)
    (за-умовою
      ((атом? форма) ні)
      ((атом? (перше форма)) (тотожне? (перше форма) (як-є printout)))
      (так ні))))

(визначити прибрати-виведення-кліпс
  (функція (форми)
    (за-умовою
      
      ((атом? форми)  (як-є ()))
      ((виведення-кліпс? (перше форми)) (прибрати-виведення-кліпс (решта форми)))
      (так (сполучити (перше форми) (прибрати-виведення-кліпс (решта форми)))))))

(визначити усі-твердження-кліпс?
  (функція (форми)
    (за-умовою
      ((атом? форми) так)
      ((твердження-кліпс? (перше форми)) (усі-твердження-кліпс? (решта форми)))
      (так ні))))

; Крок 15: одна форма assert може містити багато фактів:
; (assert (number 0) (number 1) (number 2)).
; Імпортер бере всі аргументи кожної форми, а не лише перший.
; Кілька окремих assert у тілі правила також обробляються.
; Історичний контроль — зовнішній приклад словесної задачі
; GERALD + DONALD = ROBERT із набору CLIPS.
; Порядок і кількість фактів не можна втрачати мовчки.

(визначити зібрати-висновки-кліпс
  (функція (форми)
    (за-умовою
      
      ((атом? форми)  (як-є ()))
      (так (приєднати (решта (перше форми)) (зібрати-висновки-кліпс (решта форми)))))))

(визначити правила-для-висновків-кліпс
  (функція (висновки умови)
    (за-умовою
      
      ((атом? висновки)  (як-є ()))
      (так (сполучити (сполучити (кліпс-перетворити-змінні (перше висновки)) умови)
                (правила-для-висновків-кліпс (решта висновки) умови))))))

; Step 5 (superseded — history kept, not silently erased): originally
; detected CLIPS's `(not (pattern))` conditions and skipped the whole rule,
; because `lib/forward.lisp`'s `match-conditions` had no negation-as-failure
; handling and a naively-converted `(not ...)` condition would silently
; never fire. Step 6 (`lib/forward.lisp`'s `match-one-condition`/
; `match-negated-condition`) closed that gap directly in the forward
; engine, so `not` conditions now import and run correctly — the guard
; that used to skip them has been removed rather than left as a dead,
; misleadingly-named no-op.
;
; Крок 5 (замінено — історія збережена, не тихо стерта): раніше виявляв
; CLIPS-умови `(not (шаблон))` і пропускав усе правило, бо
; `match-conditions` у `lib/forward.lisp` не мав обробки negation-as-failure,
; і наївно конвертована `(not ...)` умова мовчки ніколи б не спрацювала.
; Крок 6 (`match-one-condition`/`match-negated-condition` у
; `lib/forward.lisp`) закрив цю прогалину напряму у forward-рушії, тож умови
; `not` тепер імпортуються й працюють коректно — guard, що їх пропускав,
; прибрано, а не залишено як мертвий, оманливо названий no-op.
;
; Schritt 5 (ersetzt — Historie erhalten, nicht still gelöscht): erkannte
; ursprünglich CLIPS' `(not (muster))`-Bedingungen und übersprang die ganze
; Regel, weil `match-conditions` in `lib/forward.lisp` keine
; Negation-als-Fehlschlag-Behandlung hatte und eine naiv konvertierte
; `(not ...)`-Bedingung still nie gefeuert hätte. Schritt 6
; (`match-one-condition`/`match-negated-condition` in `lib/forward.lisp`)
; schloss diese Lücke direkt in der Forward-Engine, sodass `not`-Bedingungen
; nun korrekt importiert werden und funktionieren — der Guard, der sie
; übersprang, wurde entfernt statt als toter, irreführend benannter No-op
; zurückzubleiben.
; Template conversion runs *before* `?x`-variable conversion: slot lookup
; matches on slot names and reorders values, and a value can just as
; easily be `?x` as `earth` at this point — either way it's carried
; through positionally unchanged, then `clips-convert-vars` turns any
; `?x`-shaped value into `(var x)` afterward.
; Step 16: strip a `defrule`'s optional preamble — a docstring (a bare
; string literal) and/or a `(declare (salience N))` property, both of
; which CLIPS allows directly after the rule name and before its
; conditions. Verified against a second genuine external `.clp` file (not
; guessed): CLIPS's own "Automotive Expert System" example
; (tests/fixtures/auto-external.clp) gives every single one of its 21
; rules an empty docstring `""`, and several a `(declare (salience N))` —
; without stripping them, both landed in the condition list as if they
; were patterns to match against facts. Neither a bare string nor a
; `declare` form is ever a fact's head, so every affected rule silently
; never fired — the entire file was dead on arrival, not just one rule.
; `string?` (crates/my-lisp/src/eval/special_forms.rs) was added
; specifically to tell a docstring apart from an ordinary condition term.
;
; Salience itself (CLIPS's rule-firing priority) has no equivalent here:
; `run-multi`/`run-jtms-multi` materialize every derivable fact to a
; fixpoint regardless of order, so which rule "goes first" never changes
; the final result — dropping `declare` loses information CLIPS would use
; to order *when* things fire, never *whether* they do.
;
; Крок 16: обрізає необов'язковий преамбул `defrule` — докстрінг (голий
; рядковий літерал) і/або властивість `(declare (salience N))`, обидва
; CLIPS дозволяє одразу після імені правила, перед умовами. Перевірено на
; другому справжньому зовнішньому `.clp`-файлі (не здогадано): власний
; приклад CLIPS "Automotive Expert System"
; (tests/fixtures/auto-external.clp) дає кожному зі своїх 21 правил
; порожній докстрінг `""`, а кільком — `(declare (salience N))` — без
; обрізання обидва потрапляли у список умов, ніби були шаблонами для
; зіставлення з фактами. Ні голий рядок, ні форма `declare` ніколи не є
; головою факту, тож кожне зачеплене правило мовчки ніколи не
; спрацьовувало — весь файл був мертвий одразу, не одне правило. `string?`
; додано саме для того, щоб відрізнити докстрінг від звичайного терму умови.
;
; Сама salience (пріоритет спрацювання правил CLIPS) не має тут
; відповідника: `run-multi`/`run-jtms-multi` матеріалізують кожен
; виводимий факт до fixpoint незалежно від порядку, тож яке правило
; "спрацьовує першим" ніколи не змінює фінальний результат — відкидання
; `declare` втрачає інформацію, яку CLIPS використав би, щоб впорядкувати
; *коли* щось спрацьовує, ніколи не *чи* спрацьовує.
;
; Schritt 16: entfernt die optionale Präambel einer `defrule` — einen
; Docstring (ein bloßes String-Literal) und/oder eine `(declare (salience
; N))`-Eigenschaft, beide erlaubt CLIPS direkt nach dem Regelnamen, vor den
; Bedingungen. Verifiziert gegen eine zweite echte externe `.clp`-Datei
; (nicht geraten): CLIPS' eigenes Beispiel "Automotive Expert System"
; (tests/fixtures/auto-external.clp) gibt jeder seiner 21 Regeln einen
; leeren Docstring `""`, mehreren ein `(declare (salience N))` — ohne
; Entfernung landeten beide in der Bedingungsliste, als wären sie Muster
; zum Abgleich gegen Fakten. Weder ein bloßer String noch eine
; `declare`-Form ist je der Kopf eines Fakts, also feuerte jede betroffene
; Regel still nie — die ganze Datei war von Anfang an tot, nicht nur eine
; Regel. `string?` wurde genau dafür hinzugefügt, einen Docstring von
; einem gewöhnlichen Bedingungsterm zu unterscheiden.
;
; Salience selbst (CLIPS' Feuerpriorität für Regeln) hat hier kein
; Äquivalent: `run-multi`/`run-jtms-multi` materialisieren jeden
; ableitbaren Fakt bis zum Fixpunkt, unabhängig von der Reihenfolge, also
; ändert es nie das Endergebnis, welche Regel "zuerst dran ist" — das
; Verwerfen von `declare` verliert Information, die CLIPS nutzen würde, um
; zu ordnen, *wann* etwas feuert, nie *ob*.
; CLIPS grammar: at rule preamble, an atom other than => is the
; optional documentation datum; valid conditions and (declare ...) are pairs.
; This is a position-specific SENS structural law, NOT a general stringp.
; Do not grant the unadmitted D9:110100110 STRINGP runtime authority.
(визначити преамбула-правила-кліпс?
  (функція (форма)
    (за-умовою
      ((атом? форма)
       (за-умовою
         ((тотожне? форма (як-є =>)) ні)
         (так так)))
      ((хибне? (атом? (перше форма))) ні)
      ((тотожне? (перше форма) (як-є declare)) так)
      (так ні))))

(визначити прибрати-преамбулу-кліпс
  (функція (тіло)
    (за-умовою
      
      ((атом? тіло)  тіло)
      ((преамбула-правила-кліпс? (перше тіло)) (прибрати-преамбулу-кліпс (решта тіло)))
      (так тіло))))

; Крок 19: більше не відхиляємо правило лише через exists або
; forall: бібліотека прямого виведення вже має відповідні переходи.
; Вкладені шаблони в exists, forall, not, or та and
; рекурсивно перетворюються з іменованих слотів на позиційні.
; Кожен проміжний список обчислюємо один раз мовними функціями,
; без неоднозначної обчисленої голови лямбди чи нератифікованого LET.

(визначити кліпс-клаузи-правила-з-частин
  (функція (умови доречні шаблони)
    (за-умовою
      ((усі-твердження-кліпс? доречні)
       (правила-для-висновків-кліпс
         (кліпс-перетворити-шаблон-список (зібрати-висновки-кліпс доречні) шаблони)
         умови))
      (так (як-є ())))))

(визначити кліпс-клаузи-правила-з-розділу
  (функція (поділ шаблони)
    (кліпс-клаузи-правила-з-частин
      (кліпс-перетворити-змінні (кліпс-перетворити-шаблон-список (перше поділ) шаблони))
      (прибрати-виведення-кліпс (друге поділ))
      шаблони)))

(визначити кліпс-визначити-правило-клаузи
  (функція (форма шаблони)
    (кліпс-клаузи-правила-з-розділу
      (розділити-правило-кліпс (прибрати-преамбулу-кліпс (решта-решти форма)))
      шаблони)))

; Dispatches on one top-level CLIPS form's leading symbol. Unknown or
; not-yet-supported forms produce no clauses rather than erroring — a
; partial import of a mixed file still returns whatever it *could*
; translate. `deftemplate` itself produces no clauses (it only feeds the
; `templates` lookup `clips-import` builds once, up front).
(визначити кліпс-форма-клаузи
  (функція (форма шаблони)
    (за-умовою
      ((атом? форма) (як-є ()))
      ((хибне? (атом? (перше форма))) (як-є ()))
      ((тотожне? (перше форма) (як-є deffacts)) (кліпс-визначити-факти-клаузи форма шаблони))
      ((тотожне? (перше форма) (як-є defrule)) (кліпс-визначити-правило-клаузи форма шаблони))
      (так (як-є ())))))

; Same non-tail-call problem as `clips-facts->clauses` above, one level up:
; `(append (clips-form->clauses ...) (clips-import-forms ...))` nests one
; Rust stack frame per top-level form. `animal-external.clp` (37 forms,
; one deffacts block of 128 facts) is exactly the file that first grew
; this deep enough to crash the process outright with a real stack
; overflow rather than a graceful error — found the same "verify with a
; throwaway debug test" way as every other importer bug this file
; documents. `кліпс-сполучити-кожен-дописати` flattens one form's own clause list
; onto the running accumulator tail-recursively, so neither loop — across
; forms, or across one form's clauses — grows the native stack.
; Та сама проблема нехвостового виклику, що й у `clips-facts->clauses`
; вище, лише рівнем вище: `(append (clips-form->clauses ...)
; (clips-import-forms ...))` вкладає один Rust-стек-фрейм на кожну
; верхньорівневу форму. `animal-external.clp` (37 форм, один блок
; deffacts зі 128 фактів) — саме той файл, що вперше виріс достатньо
; глибоко, щоб реально впасти зі stack overflow замість коректної
; помилки — знайдено тим самим способом "спершу тимчасовий debug-тест",
; що й усі інші баги імпортера в цьому файлі. `кліпс-сполучити-кожен-дописати`
; сплющує список clause однієї форми на робочий акумулятор хвостово-
; рекурсивно, тож жоден із циклів — ні по формах, ні по clause однієї
; форми — не росте нативний стек.
; Dasselbe Nicht-Tail-Call-Problem wie bei `clips-facts->clauses` oben,
; nur eine Ebene höher: `(append (clips-form->clauses ...)
; (clips-import-forms ...))` verschachtelt einen Rust-Stack-Frame pro
; Top-Level-Form. `animal-external.clp` (37 Formen, ein deffacts-Block
; mit 128 Fakten) ist genau die Datei, die das erstmals tief genug wachsen
; ließ, um mit einem echten Stack-Overflow abzustürzen statt einen
; ordentlichen Fehler zu liefern — gefunden auf demselben Weg "erst ein
; Wegwerf-Debug-Test" wie jeder andere Importer-Bug in dieser Datei.
; `кліпс-сполучити-кожен-дописати` glättet die Clause-Liste einer Form tail-rekursiv
; auf den laufenden Akkumulator, sodass weder die Schleife über die Formen
; noch die über die Clauses einer Form den nativen Stack wachsen lässt.
(визначити кліпс-сполучити-кожен-дописати
  (функція (елементи накопичені)
    (за-умовою
      
      ((атом? елементи)  накопичені)
      (так (кліпс-сполучити-кожен-дописати (решта елементи) (сполучити (перше елементи) накопичені))))))

(визначити кліпс-імпорт-форм-дописати
  (функція (форми шаблони накопичені)
    (за-умовою
      ((атом? форми) (зворот накопичені))
      (так (кліпс-імпорт-форм-дописати
           (решта форми) шаблони
           (кліпс-сполучити-кожен-дописати (кліпс-форма-клаузи (перше форми) шаблони) накопичені))))))

(визначити кліпс-імпорт-форми
  (функція (форми шаблони)
    (кліпс-імпорт-форм-дописати форми шаблони (як-є ()))))

(визначити кліпс-імпорт
  (функція (форми)
    (кліпс-імпорт-форми форми (кліпс-шаблони-з-форми форми))))

; Крок 4: імпорт справжнього файла вихідного коду CLIPS.
; Читання файла повертає текст, читання всіх форм — список
; верхньорівневих даних. Решту обробляє кліпс-імпорт.
; Це той самий шлях перетворення, що й для цитованого
; списку форм, переданого безпосередньо викликачем.

(визначити кліпс-імпорт-файл
  (функція (шлях)
    (кліпс-імпорт (читати-всі (читати-файл шлях)))))

; D9 exact-width Ukrainian projections of native CLIPS S-expression importer.
; Source laws are the Lisp closures above; no new parser, Rust semantics or opcode.
; D9:010110100
(визначити clips-deftemplate-форма? кліпс-визначити-шаблон-форма?)
; D9:001110111
(визначити clips-слот-імена кліпс-слот-імена)
; D9:001100110
(визначити clips-deftemplate-слоти кліпс-визначити-шаблон-слоти)
; D9:001010011
(визначити clips-шаблони-з-форми кліпс-шаблони-з-форми)
; D9:001010101
(визначити clips-шаблон-слот-порядок кліпс-шаблон-слот-порядок)
; D9:010001111
(визначити clips-перетворити-шаблон кліпс-перетворити-шаблон)
; D9:010001101
(визначити clips-перетворити-шаблон-список кліпс-перетворити-шаблон-список)
; D9:010111000
(визначити clips-факт-клауза кліпс-факт-клауза)
; D9:001110001
(визначити clips-факти-клаузи кліпс-факти-клаузи)
; D9:010010000
(визначити clips-deffacts-клаузи кліпс-визначити-факти-клаузи)
; D9:001110100
(визначити clips-змінна? кліпс-змінна?)
; D9:101000111
(визначити clips-перетворити-змінні кліпс-перетворити-змінні)

; D9: точні 9-бітні ідентичності — lib/domains/d9.lisp.
; Чинні закони залишаються в SENS-донорі вище, не в Rust чи Zig.
; Ці DEFINE зв'язують українські поверхні; це не автоматичний D9 opcode.
; D9:001101010
(визначити clips-deftemplate-ім'я кліпс-визначити-шаблон-ім'я)
; D9:001011110
(визначити clips-змінна-терм кліпс-змінна-терм)
; D9:010001001
(визначити clips-defrule-клаузи кліпс-визначити-правило-клаузи)
; D9:010100000
(визначити clips-форма-клаузи кліпс-форма-клаузи)

; Українські D9-поверхні. Точні коди — lib/domains/d9.lisp.
; Виконання належить уже визначеним SENS-функціям, не Rust registry/opcode.
; D9:001000001
(визначити clips-імпорт-форми кліпс-імпорт-форми)
; D9:001011000
(визначити clips-імпорт кліпс-імпорт)
; D9:001000100
(визначити clips-імпорт-файл кліпс-імпорт-файл)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити clips-all-asserts? усі-твердження-кліпс?)
(визначити clips-assert-conclusions зібрати-висновки-кліпс)
(визначити clips-assert-form? твердження-кліпс?)
(визначити clips-clauses-for-conclusions правила-для-висновків-кліпс)
(визначити clips-convert-template кліпс-перетворити-шаблон)
(визначити clips-convert-template-list кліпс-перетворити-шаблон-список)
(визначити clips-convert-vars кліпс-перетворити-змінні)
(визначити clips-deffacts->clauses кліпс-визначити-факти-клаузи)
(визначити clips-defrule->clauses кліпс-визначити-правило-клаузи)
(визначити clips-deftemplate-form? кліпс-визначити-шаблон-форма?)
(визначити clips-deftemplate-name кліпс-визначити-шаблон-ім'я)
(визначити clips-deftemplate-slots кліпс-визначити-шаблон-слоти)
(визначити clips-drop-printouts прибрати-виведення-кліпс)
(визначити clips-fact-clause кліпс-факт-клауза)
(визначити clips-facts->clauses кліпс-факти-клаузи)
(визначити clips-form->clauses кліпс-форма-клаузи)
(визначити clips-import кліпс-імпорт)
(визначити clips-import-forms кліпс-імпорт-форми)
(визначити clips-lookup-slot-value знайти-значення-слота-кліпс)
(визначити clips-positional-args позиційні-аргументи-кліпс)
(визначити clips-printout-form? виведення-кліпс?)
(визначити clips-rule-preamble-form? преамбула-правила-кліпс?)
(визначити clips-slot-name кліпс-слот-ім'я)
(визначити clips-slot-names кліпс-слот-імена)
(визначити clips-split-at-arrow розділити-правило-кліпс)
(визначити clips-strip-module-prefix прибрати-префікс-модуля-кліпс)
(визначити clips-strip-rule-preamble прибрати-преамбулу-кліпс)
(визначити clips-template-slot-order кліпс-шаблон-слот-порядок)
(визначити clips-templates-from-forms кліпс-шаблони-з-форми)
(визначити clips-var-term кліпс-змінна-терм)
(визначити clips-var? кліпс-змінна?)
; Зовнішня історична назва лишається посиланням на вже визначену українську функцію.
(визначити clips-import-file кліпс-імпорт-файл)
