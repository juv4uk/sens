; Відтворення таблиці функцій ECO-CANON-1 (my-lisp#75) із першоджерела.
; Генератор написано самою мовою СЕНС (2026-09-12). Він замінив
; вилучений scripts/generate-function-table.py за завданням #76.
; Інструменти репозиторію створюємо мовою СЕНС, а не шляхом
; додавання нових сценаріїв Python для подальшого перенесення.
;
; Історичний плаский реєстр відтворюємо лише для перевірки й міграції.
; Канонічна тотожність — точний домен, слово та допущений закон.
; Кількість рядків і давня восьмибітна позиція не є інваріантами мови.
; Історичний реєстр читаємо як дані Lisp, а не текстовим пошуком:
; сторонній розбирач для читання коректного джерела СЕНС не потрібен.
;
; The human projection may also join processor-specific realization metadata.
; That metadata is deliberately NOT semantic authority: the Intel Core i5-6400
; profile is keyed by existing semantic IDs and only says how an already-known
; meaning can reach that processor's x86-64 ISA.
;
; Writes two generated views directly (write-file is language-owned,
; lib/fs.lisp, over the host's read-file-bytes/write-file-bytes):
;   lib/generated/function-table.lisp  (schema ft/2, machine-readable projection)
;   docs/generated/function-table.md  (human table, column order
;     ук -> укр -> English -> Sanskrit -> Intel Core i5-6400 / Skylake)
;
; Usage (from the repo root):
;   cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp
;
; `ук` is the current/compact Ukrainian surface.
; `укр` is the full Ukrainian peer surface of the SAME semantic identity.
; Both are read directly from semantic-registry.lisp; this generator never
; invents names and never duplicates `укр` under another full-UK column.

; Registry surfaces are fixed two-element rows: (namespace spelling-or-()).
; Reader-sensitive spellings such as apostrophe are serialized as strings, so the
; registry remains ordinary re-readable Lisp data without a special reconstruction path.
(визначити форма-реєстру (перше (читати-всі (читати-файл "lib/surface/semantic-registry.lisp"))))
(визначити рядки-реєстру форма-реєстру)
; Historical rows are retained only for migration/provenance consumers.
; Their eight-bit coordinates do not create canonical language identity.
(визначити записи-реєстру рядки-реєстру)

; Processor realization projection. Its rows never create an identity: they
; may only annotate IDs that already exist in `entries` above.
(визначити форма-машинного-профілю
  (перше (читати-всі (читати-файл "lib/machine/intel-core-i5-6400.lisp"))))

(визначити знайти-розділ
  (функція (назва розділи)
    (за-умовою
      ((атом? розділи) (як-є ()))
      
      ((тотожне? (перше (перше розділи)) назва) (перше розділи))
      ((атом? (як-є ())) (знайти-розділ назва (решта розділи))))))

(визначити машинні-рядки
  (решта (знайти-розділ (як-є rows) (решта форма-машинного-профілю))))

(визначити знайти-машинний-рядок
  (функція (історичний-код рядки)
    (за-умовою
      ((атом? рядки) (як-є ()))
      
      ((однакові? (перше (перше рядки)) історичний-код) (перше рядки))
      ((атом? (як-є ())) (знайти-машинний-рядок історичний-код (решта рядки))))))

(визначити машинний-шлях
  (функція (історичний-код)
    (нехай ((рядок (знайти-машинний-рядок історичний-код машинні-рядки)))
      (за-умовою ((атом? рядок) "()") ((атом? (як-є ())) (третє рядок))))))

; Historical (McCarthy 1960 / Lisp 1.5) realization projection. Its rows
; never create an identity: they may only annotate IDs that already exist
; in `entries` above. Reverse-authority is forbidden by the contract file
; itself -- a historical name never mints a new my-lisp SID.
(визначити форма-історичного-профілю
  (перше (читати-всі (читати-файл "contracts/core1-historical-sid-map.lisp"))))

(визначити історичні-рядки
  (решта (знайти-розділ (як-є rows) (решта форма-історичного-профілю))))

(визначити знайти-історичний-рядок
  (функція (історичний-код рядки)
    (за-умовою
      ((атом? рядки) (як-є ()))
      
      ((однакові? (друге (перше рядки)) історичний-код) (перше рядки))
      ((атом? (як-є ())) (знайти-історичний-рядок історичний-код (решта рядки))))))

(визначити позначка-маккарті
  (функція (історичний-код)
    (нехай ((рядок (знайти-історичний-рядок історичний-код історичні-рядки)))
      (за-умовою ((атом? рядок) "()") ((атом? (як-є ())) (поєднати-рядки (значення-у-текст (четверте рядок)) " (" (значення-у-текст (п'ятий рядок)) ")"))))))

; Назва проєкції зазвичай є символом: канонічний друкар
; перетворює його на текстове представлення без обгортки.
; Відновлений апостроф вище вже є рядком.
; Для людиночитної таблиці Markdown апостроф подається без змін.
(визначити текст-слова-проєкції
  (функція (слово)
    (за-умовою
      ((однакові? слово (як-є ())) "()")
      ((тотожне? (класифікувати-рядкове-значення слово) (class-membership string member))
       слово)
      ((тотожне? (класифікувати-рядкове-значення слово) (class-membership string nonmember))
       (значення-у-текст слово)))))

; Для машинно-читного виходу .lisp не можна вставляти апостроф
; без цитування: читач сприйме його як синтаксис цитати.
; Канонічний друкар зберігає рядок екранованим і придатним для
; повторного читання, тоді як символ лишається без обгортки.
; Тут використовується та сама ратифікована функція значення-у-текст.
(визначити текст-слова-проєкції-сенс значення-у-текст)

; --- string-append is exactly binary; this repo's scripts routinely need
; more pieces joined than that, so a small variadic wrapper over reduce.
(визначити поєднати-рядки
  (функція аргументи (згорнути (функція (накопичувач частина) (рядок-додати накопичувач частина)) "" аргументи)))

; SID already arrives from the registry as an exact 8-bit string. This generator
; must preserve it verbatim; formatting identity is owned by the registry.

; --- surfaces are fixed (lang word) slots; word is spelling or () ---
(визначити знайти-проєкцію
  (функція (мова проєкції)
    (за-умовою
      ((атом? проєкції) (як-є ()))
      
      ((тотожне? (перше (перше проєкції)) мова) (перше проєкції))
      ((атом? (як-є ())) (знайти-проєкцію мова (решта проєкції))))))

(визначити слово-проєкції
  (функція (запис-проєкції)
    (за-умовою ((атом? запис-проєкції) (як-є ())) ((атом? (як-є ())) (перше (решта запис-проєкції))))))

(визначити отримати-проєкцію
  (функція (мова проєкції)
    (слово-проєкції (знайти-проєкцію мова проєкції))))

(визначити проєкція-придатна?
  (функція (слово)
    (хибне? (однакові? слово (як-є ())))))

; --- formal identity stub: first present name among en/ук/sa, else bare id ---
; SID is already a first-class exact eight-bit identity. Its canonical printer
; preserves the exact spelling including leading zeroes; do not reinterpret it
; as arithmetic data merely to reconstruct the same source identity.
(визначити історичні-біти-ідентифікатора
  (функція (історичний-код)
    (значення-у-текст історичний-код)))

(визначити формальна-заготовка
  (функція (історичний-код проєкції)
    (нехай-послідовно ((англійська-назва (отримати-проєкцію (як-є en) проєкції))
           (ук (отримати-проєкцію (як-є ук) проєкції))
           (санскритська-назва (отримати-проєкцію (як-є sa) проєкції)))
      (за-умовою
        ((проєкція-придатна? англійська-назва)
         (поєднати-рядки "identity:" (історичні-біти-ідентифікатора історичний-код) "/surface:" (текст-слова-проєкції англійська-назва)))
        ((проєкція-придатна? ук)
         (поєднати-рядки "identity:" (історичні-біти-ідентифікатора історичний-код) "/surface:" (текст-слова-проєкції ук)))
        ((проєкція-придатна? санскритська-назва)
         (поєднати-рядки "identity:" (історичні-біти-ідентифікатора історичний-код) "/surface:" (текст-слова-проєкції санскритська-назва)))
        ((атом? (як-є ())) (рядок-додати "identity:" (історичні-біти-ідентифікатора історичний-код)))))))

; Historical projection intentionally has no 256-row completeness law.
; Exact domains grow under their own widths, occupancy maps, and admitted laws.

; --- string-join with newline, since core.lisp has none yet. Accumulator-
; based (not "car + recurse-in-argument-position"), matching core.lisp's own
; map-onto/reverse-onto/length-onto pattern -- a naive recursive version
; is not tail-recursive (the recursive call sits inside str+'s argument
; list, not in tail position) and overflows the host stack well before
; this registry's complete row set.
(визначити поєднати-рядки-з-новим-рядком-до
  (функція (текстові-рядки накопичувач)
    (за-умовою
      ((атом? текстові-рядки) накопичувач)
      
      ((тотожне? накопичувач "") (поєднати-рядки-з-новим-рядком-до (решта текстові-рядки) (перше текстові-рядки)))
      ((атом? (як-є ())) (поєднати-рядки-з-новим-рядком-до (решта текстові-рядки) (поєднати-рядки накопичувач "
" (перше текстові-рядки)))))))

(визначити поєднати-рядки-з-новим-рядком (функція (текстові-рядки) (поєднати-рядки-з-новим-рядком-до текстові-рядки "")))

(визначити подати-рядок-сенс
  (функція (запис)
    (нехай-послідовно ((історичний-код (перше запис))
           (проєкції (решта запис))
           (ук (отримати-проєкцію (як-є ук) проєкції))
           (укр (отримати-проєкцію (як-є укр) проєкції))
           (англійська-назва (отримати-проєкцію (як-є en) проєкції))
           (санскритська-назва (отримати-проєкцію (як-є sa) проєкції))
           (символьна-назва (отримати-проєкцію (як-є sym) проєкції))
           (формальна-форма (формальна-заготовка історичний-код проєкції)))
      (поєднати-рядки
        "  (" (історичні-біти-ідентифікатора історичний-код) " " формальна-форма
        " (ук " (текст-слова-проєкції-сенс ук) ")"
        " (укр " (текст-слова-проєкції-сенс укр) ")"
        " (en " (текст-слова-проєкції-сенс англійська-назва) ")"
        " (sa " (текст-слова-проєкції-сенс санскритська-назва) ")"
        " (sym " (текст-слова-проєкції-сенс символьна-назва) ")"
        " my-lisp)"))))

(визначити подати-рядок-довідника
  (функція (запис)
    (нехай-послідовно ((історичний-код (перше запис))
           (проєкції (решта запис))
           (ук (отримати-проєкцію (як-є ук) проєкції))
           (укр (отримати-проєкцію (як-є укр) проєкції))
           (англійська-назва (отримати-проєкцію (як-є en) проєкції))
           (санскритська-назва (отримати-проєкцію (як-є sa) проєкції))
           (символьна-назва (отримати-проєкцію (як-є sym) проєкції)))
      (поєднати-рядки
        "| `" (історичні-біти-ідентифікатора історичний-код) "` | " (текст-слова-проєкції ук)
        " | " (текст-слова-проєкції укр)
        " | " (текст-слова-проєкції англійська-назва)
        " | " (текст-слова-проєкції санскритська-назва)
        " | " (текст-слова-проєкції символьна-назва)
        " | " (машинний-шлях історичний-код)
        " | " (позначка-маккарті історичний-код) " |"))))

(визначити заголовок-сенс
  (список
    "; GENERATED — DO NOT EDIT BY HAND"
    "; HISTORICAL MIGRATION PROJECTION — NOT SEMANTIC AUTHORITY"
    "; Donor: lib/surface/semantic-registry.lisp"
    "; Generator: scripts/generate-function-table.lisp"
    "; Schema ft/2: (legacy-bitstring formal ук укр en sa sym projection)"
    "; ук = current Ukrainian; укр = full Ukrainian peer surface"
    "; Display order for humans: ук → укр → English → Sanskrit"
    "; projection = historical/migration review only"
    ""
    "(ft/2"))

(визначити тіло-сенс (поєднати-рядки-з-новим-рядком (приєднати заголовок-сенс (відобразити подати-рядок-сенс записи-реєстру))))
(визначити вивід-сенс (рядок-додати тіло-сенс "
)
"))

(визначити заголовок-довідника
  (список
    "# Function table (generated projection)"
    ""
    "**Status:** historical migration projection. Canonical identity comes from exact domains and admitted laws, not this flat table."
    ""
    "**Machine projection:** `lib/machine/intel-core-i5-6400.lisp` — physical execution paths only; it does not create language meaning."
    ""
    "**Historical projection:** `contracts/core1-historical-sid-map.lisp` — one-way SID → McCarthy 1960 / Lisp 1.5 mechanism comparison, pinned against `juv4uk/mccarthy-eval`; it never mints a new identity and does not create language meaning."
    ""
    "Regenerate: `cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp`"
    ""
    "| ID | ук | укр | English | Sanskrit | Symbol | Intel Core i5-6400 / Skylake | McCarthy 1960 / Lisp 1.5 (Core1) |"
    "|----|----|-----|---------|----------|--------|------------------------------|-----------------------------------|"))

(визначити тіло-довідника (поєднати-рядки-з-новим-рядком (приєднати заголовок-довідника (відобразити подати-рядок-довідника записи-реєстру))))
(визначити вивід-довідника (рядок-додати тіло-довідника "
"))

(визначити шлях-виводу-сенс "lib/generated/function-table.lisp")
(визначити шлях-виводу-довідника "docs/generated/function-table.md")

(визначити записати-проєкції
  (функція ()
    (друге
      (список
        (записати-файл шлях-виводу-сенс вивід-сенс)
        (записати-файл шлях-виводу-довідника вивід-довідника)
        (друкувати
          (поєднати-рядки
            "function-table: "
            (число-рядок (довжина записи-реєстру))
            " historical projection rows written"))))))

; The projection payloads and argv selector below are strings, hence atoms.
; Use exact D3:101 EQ (3 bits), not the wider D8:11110111 structural EQUAL.
; This is a source-identity narrowing only; no physical T5 size claim follows.
(визначити перевірити-проєкції
  (функція ()
    (нехай ((чинний-сенс (читати-файл шлях-виводу-сенс))
          (чинний-довідник (читати-файл шлях-виводу-довідника)))
      (за-умовою
        ((тотожне? чинний-сенс вивід-сенс)
         (за-умовою
           ((тотожне? чинний-довідник вивід-довідника)
            (друкувати
              (поєднати-рядки
                "function-table: "
                (число-рядок (довжина записи-реєстру))
                " historical projection rows current")))
           ((атом? (як-є ()))
            (друге
              (список
                (друкувати "function-table markdown projection is stale")
                (перше (як-є ())))))))
        ((атом? (як-є ()))
         (друге
           (список
             (друкувати "function-table Lisp projection is stale")
             (перше (як-є ())))))))))

(за-умовою
  ((атом? *argv*)
   (записати-проєкції))
  ((тотожне? (перше *argv*) "--check")
   (перевірити-проєкції))
  ((атом? (як-є ()))
   (записати-проєкції)))
