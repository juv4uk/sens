; scripts/generate-function-table.lisp — regenerate the ECO-CANON-1 function
; table (my-lisp#75) from its real source of truth, written in my-lisp
; itself (2026-09-12), replacing the retired scripts/generate-function-table.py
; per issue #76 (ECO-LISP-SCRIPTS-1): repo-owned tooling must not add new
; Python scripting surface, and tooling should be written directly in
; my-lisp/wsm rather than migrated later.
;
; This script renders the historical flat registry only as a migration/review
; projection. Canonical language authority is exact domain identity + admitted
; law. Row count and legacy eight-bit position are not language invariants.
; Reads the historical surface registry as ordinary my-lisp data
; (read-file/read-all), not text/regex — the registry is already valid
; my-lisp source, so no foreign parser is needed.
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
(визначити записи рядки-реєстру)

; Processor realization projection. Its rows never create an identity: they
; may only annotate IDs that already exist in `entries` above.
(визначити форма-профілю-машини
  (перше (читати-всі (читати-файл "lib/machine/intel-core-i5-6400.lisp"))))

(визначити знайти-розділ
  (функція (назва розділи)
    (за-умовою
      ((атом? розділи) (як-є ()))
      
      ((тотожне? (перше (перше розділи)) назва) (перше розділи))
      ((атом? (як-є ())) (знайти-розділ назва (решта розділи))))))

(визначити рядки-машини
  (решта (знайти-розділ (як-є rows) (решта форма-профілю-машини))))

(визначити знайти-рядок-машини
  (функція (ід рядки)
    (за-умовою
      ((атом? рядки) (як-є ()))
      
      ((однакові? (перше (перше рядки)) ід) (перше рядки))
      ((атом? (як-є ())) (знайти-рядок-машини ід (решта рядки))))))

(визначити шлях-машини
  (функція (ід)
    (нехай ((рядок (знайти-рядок-машини ід рядки-машини)))
      (за-умовою ((атом? рядок) "()") ((атом? (як-є ())) (третє рядок))))))

; Historical (McCarthy 1960 / Lisp 1.5) realization projection. Its rows
; never create an identity: they may only annotate IDs that already exist
; in `entries` above. Reverse-authority is forbidden by the contract file
; itself -- a historical name never mints a new my-lisp SID.
(визначити форма-історичного-профілю
  (перше (читати-всі (читати-файл "contracts/core1-historical-sid-map.lisp"))))

(визначити рядки-історичні
  (решта (знайти-розділ (як-є rows) (решта форма-історичного-профілю))))

(визначити знайти-історичний-рядок
  (функція (ід рядки)
    (за-умовою
      ((атом? рядки) (як-є ()))
      
      ((однакові? (друге (перше рядки)) ід) (перше рядки))
      ((атом? (як-є ())) (знайти-історичний-рядок ід (решта рядки))))))

(визначити мітка-макарті
  (функція (ід)
    (нехай ((рядок (знайти-історичний-рядок ід рядки-історичні)))
      (за-умовою ((атом? рядок) "()") ((атом? (як-є ())) (рядок+ (значення-у-текст (четверте рядок)) " (" (значення-у-текст (п'ятий рядок)) ")"))))))

; A surface word is usually a symbol (write-to-string strips the
; Lisp-level Symbol wrapping down to bare text); the reconstructed
; apostrophe case above is already a plain string. For prose contexts
; (the human .md table) the bare apostrophe is fine either way.
(визначити текст-слова-поверхні
  (функція (слово)
    (за-умовою
      ((однакові? слово (як-є ())) "()")
      ((тотожне? (класифікувати-рядкове-значення слово) (class-membership string member))
       слово)
      ((тотожне? (класифікувати-рядкове-значення слово) (class-membership string nonmember))
       (значення-у-текст слово)))))

; For the machine-readable .lisp output specifically, a bare apostrophe
; word must NOT be re-embedded unquoted: a future reader of this
; generated file would hit the exact same "'" quote-shorthand collision
; this script itself just worked around on the way in. write-to-string
; already does exactly the right thing per Value type -- a String gets
; quoted/escaped (read-back-safe), a Symbol stays bare -- so this is
; just write-to-string directly, named for what it's used for here.
(визначити wsm-текст-слова-поверхні значення-у-текст)

; --- string-append is exactly binary; this repo's scripts routinely need
; more pieces joined than that, so a small variadic wrapper over reduce.
(визначити рядок+
  (функція аргументи (згорнути (функція (накопичувач с) (рядок-додати накопичувач с)) "" аргументи)))

; SID already arrives from the registry as an exact 8-bit string. This generator
; must preserve it verbatim; formatting identity is owned by the registry.

; --- surfaces are fixed (lang word) slots; word is spelling or () ---
(визначити знайти-поверхню
  (функція (мова поверхні)
    (за-умовою
      ((атом? поверхні) (як-є ()))
      
      ((тотожне? (перше (перше поверхні)) мова) (перше поверхні))
      ((атом? (як-є ())) (знайти-поверхню мова (решта поверхні))))))

(визначити слово-поверхні
  (функція (запис-поверхні)
    (за-умовою ((атом? запис-поверхні) (як-є ())) ((атом? (як-є ())) (перше (решта запис-поверхні))))))

(визначити отримати-поверхню
  (функція (мова поверхні)
    (слово-поверхні (знайти-поверхню мова поверхні))))

(визначити поверхня-придатна?
  (функція (слово)
    (хибне? (однакові? слово (як-є ())))))

; --- formal identity stub: first present name among en/ук/sa, else bare id ---
; SID is already a first-class exact eight-bit identity. Its canonical printer
; preserves the exact spelling including leading zeroes; do not reinterpret it
; as arithmetic data merely to reconstruct the same source identity.
(визначити біти-ід
  (функція (ід)
    (значення-у-текст ід)))

(визначити заглушка-формального
  (функція (ід поверхні)
    (нехай-послідовно ((англ (отримати-поверхню (як-є en) поверхні))
           (ук (отримати-поверхню (як-є ук) поверхні))
           (санскр (отримати-поверхню (як-є sa) поверхні)))
      (за-умовою
        ((поверхня-придатна? англ)
         (рядок+ "identity:" (біти-ід ід) "/surface:" (текст-слова-поверхні англ)))
        ((поверхня-придатна? ук)
         (рядок+ "identity:" (біти-ід ід) "/surface:" (текст-слова-поверхні ук)))
        ((поверхня-придатна? санскр)
         (рядок+ "identity:" (біти-ід ід) "/surface:" (текст-слова-поверхні санскр)))
        ((атом? (як-є ())) (рядок-додати "identity:" (біти-ід ід)))))))

; Historical projection intentionally has no 256-row completeness law.
; Exact domains grow under their own widths, occupancy maps, and admitted laws.

; --- string-join with newline, since core.lisp has none yet. Accumulator-
; based (not "car + recurse-in-argument-position"), matching core.lisp's own
; map-onto/reverse-onto/length-onto pattern -- a naive recursive version
; is not tail-recursive (the recursive call sits inside str+'s argument
; list, not in tail position) and overflows the host stack well before
; this registry's complete row set.
(визначити зєднати-новим-рядком-у
  (функція (рядки-рядків накопичувач)
    (за-умовою
      ((атом? рядки-рядків) накопичувач)
      
      ((тотожне? накопичувач "") (зєднати-новим-рядком-у (решта рядки-рядків) (перше рядки-рядків)))
      ((атом? (як-є ())) (зєднати-новим-рядком-у (решта рядки-рядків) (рядок+ накопичувач "
" (перше рядки-рядків)))))))

(визначити зєднати-новим-рядком (функція (рядки-рядків) (зєднати-новим-рядком-у рядки-рядків "")))

(визначити відрендерити-wsm-рядок
  (функція (запис)
    (нехай-послідовно ((ід (перше запис))
           (поверхні (решта запис))
           (ук (отримати-поверхню (як-є ук) поверхні))
           (укр (отримати-поверхню (як-є укр) поверхні))
           (англ (отримати-поверхню (як-є en) поверхні))
           (санскр (отримати-поверхню (як-є sa) поверхні))
           (симв (отримати-поверхню (як-є sym) поверхні))
           (формальне (заглушка-формального ід поверхні)))
      (рядок+
        "  (" (біти-ід ід) " " формальне
        " (ук " (wsm-текст-слова-поверхні ук) ")"
        " (укр " (wsm-текст-слова-поверхні укр) ")"
        " (en " (wsm-текст-слова-поверхні англ) ")"
        " (sa " (wsm-текст-слова-поверхні санскр) ")"
        " (sym " (wsm-текст-слова-поверхні симв) ")"
        " my-lisp)"))))

(визначити відрендерити-md-рядок
  (функція (запис)
    (нехай-послідовно ((ід (перше запис))
           (поверхні (решта запис))
           (ук (отримати-поверхню (як-є ук) поверхні))
           (укр (отримати-поверхню (як-є укр) поверхні))
           (англ (отримати-поверхню (як-є en) поверхні))
           (санскр (отримати-поверхню (як-є sa) поверхні))
           (симв (отримати-поверхню (як-є sym) поверхні)))
      (рядок+
        "| `" (біти-ід ід) "` | " (текст-слова-поверхні ук)
        " | " (текст-слова-поверхні укр)
        " | " (текст-слова-поверхні англ)
        " | " (текст-слова-поверхні санскр)
        " | " (текст-слова-поверхні симв)
        " | " (шлях-машини ід)
        " | " (мітка-макарті ід) " |"))))

(визначити wsm-заголовок
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

(визначити wsm-тіло (зєднати-новим-рядком (приєднати wsm-заголовок (відобразити відрендерити-wsm-рядок записи))))
(визначити wsm-вихід (рядок-додати (рядок-додати wsm-тіло "
)") "
"))

(визначити md-заголовок
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

(визначити md-тіло (зєднати-новим-рядком (приєднати md-заголовок (відобразити відрендерити-md-рядок записи))))
(визначити md-вихід (рядок-додати md-тіло "
"))

(визначити wsm-шлях-виходу "lib/generated/function-table.lisp")
(визначити md-шлях-виходу "docs/generated/function-table.md")

(визначити записати-проєкції
  (функція ()
    (друге
      (список
        (записати-файл wsm-шлях-виходу wsm-вихід)
        (записати-файл md-шлях-виходу md-вихід)
        (друкувати
          (рядок+
            "function-table: "
            (число-рядок (довжина записи))
            " historical projection rows written"))))))

; The projection payloads and argv selector below are strings, hence atoms.
; Use exact D3:101 EQ (3 bits), not the wider D8:11110111 structural EQUAL.
; This is a source-identity narrowing only; no physical T5 size claim follows.
(визначити перевірити-проєкції
  (функція ()
    (нехай ((поточний-wsm (читати-файл wsm-шлях-виходу))
          (поточний-md (читати-файл md-шлях-виходу)))
      (за-умовою
        ((тотожне? поточний-wsm wsm-вихід)
         (за-умовою
           ((тотожне? поточний-md md-вихід)
            (друкувати
              (рядок+
                "function-table: "
                (число-рядок (довжина записи))
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
