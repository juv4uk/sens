; Машинно-читаний інвентар історичної англомовної публічної поверхні.
; Файл класифікує назви за їхньою роллю, але не визначає
; українських назв і не створює нових семантичних тотожностей.

(uk-surface-inventory
  (schema uk-surface-inventory/1)
  (eligibility-rules
    ((public (user-program-name documented-or-exercised-as-api))
     (internal (implementation-helper accumulator-worker bootstrap-mechanism))
     (compatibility (supported-historical-user-name))
     (predicate (public-question-with-domain-owned-result))
     (symbolic-sugar (compact-notation-over-word-first-public-name))))
  (public
    ((canon (quote атом? eq? cons car cdr cond))
     (necessary-forms (define lambda))
     (language-macros (defmacro))
     (compatibility-forms (def))
     (root-builtins
       (+ - * / < = > car cdr cons env eq?
        eval f32-buffer i32-buffer json-parse make-vector
        mono-ns ntp-query-raw numeric-buffer-length numeric-buffer-map
        numeric-buffer-ref numeric-buffer-type numeric-buffer? princ print read
        read-all sha256-hex string->codepoint string->symbol string-append
        string-first string-rest string-slice string<? string? symbol->string
        timezone-declarations-raw unix-time-now vector vector-length vector-ref
        vector-set! write-to-string codepoint->string))
     ; Із 11.09.2026 abs/max/max-list/min/min-list належать бібліотеці,
     ; а не кореневим примітивам: їхній механізм перенесено
     ; з Rust builtins.rs до lib/core.lisp. Джерело доказу:
     ; docs/VERTICAL-SLICE-1-ABS-MIN-MAX-2026-09-11.md.
     ; Інвентар оновлено після виявлення історичної невідповідності.
     (core-library
       (модуль identity binary list not? and or gensym pair second third fourth cadddr fifth
        caar cadr cddr length reverse append map filter reduce let equal? max
        max-list member? min min-list assoc let* nth string<? symbol? quotient mod
        divmod <= >= number->string -> ->> isqrt sqrt
        null? subst sublis maplist apply
        answer-atom answer-eq answer-not answer-and answer-or answer-weaken))))
  ; Українські слова є основною людиночитаною поверхнею.
  ; Математичні знаки — лише необов'язковий скорочений запис
  ; тих самих уже визначених операцій.
  (symbolic-sugar (+ - * / < = > <= >=))
  (internal
    ((bootstrap (макрос))
     (host-capabilities (читати-сирий-текст-файла записати-байти-файла))
     (core-library
       (довжина-до reverse-onto map-onto filter-onto знайти-найбільший-блок-частки
        перевірити-неспадання-значень? перевірити-незростання-значень?
        уточнити-корінь-ітерацією крок-цілого-кореня truthy?
        класифікувати-рядкове-значення порівняти-рядки-за-кодовими-точками класифікувати-непорожність-рядка
        знайти-пару-підстановки підготувати-цитовані-аргументи
        сталі-відповідники-за-адресами знайти-групу-відповідників-за-адресою
        стан-привязки-відповідника відсутні-відповідники
        побудувати-визначення-відповідників матеріалізувати-сталі-відповідники))))
  ; Every future Ukrainian spelling for these public predicates ends in ?.
  (public-predicates
    (атом? eq? < = > numeric-buffer? string<? string? not? equal? member?
     string-empty? string-prefix? string-contains? symbol? null? <= >=)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити модуль abs)
(визначити атом? atom?)
(визначити довжина-до length-onto)
