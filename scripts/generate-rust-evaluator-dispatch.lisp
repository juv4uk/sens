; Генератор механічної проєкції необхідних форм обчислювача мовою СЕНС.
; Джерело законів: lib/surface/function-signatures.lisp, поле (form ...) рядка.
; Раст отримує тільки похідні дані виконання, а не власне визначення законів.
; Англомовні рядки вихідного Расту, шляхів і протоколів не перекладати.
;
; Запуск:
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(визначити шлях-джерела "lib/surface/function-signatures.lisp")
(визначити шлях-результату "crates/sens/src/eval/necessary_forms_generated.rs")

(визначити зчепити-рядки
  (функція аргументи
    (згорнути (функція (накопичувач частина) (рядок-додати накопичувач частина)) "" аргументи)))

;; Особливі форми — рядки таблиці з полем (form lambda|define).
(визначити усі-рядки
  (перше (читати-всі (читати-файл шлях-джерела))))

(визначити форма-рядка
  (функція (рядок)
    (друге (знайти-за-ключем (як-є form) (решта рядок)))))

(визначити рядки-форм
  (функція (залишок)
    (за-умовою
      ((атом? залишок)
       (як-є ()))
      ((атом? (як-є ()))
       (за-умовою
         ((атом? (знайти-за-ключем (як-є form) (решта (перше залишок))))
          (рядки-форм (решта залишок)))
         ((атом? (як-є ()))
          (сполучити (перше залишок) (рядки-форм (решта залишок)))))))))

(визначити рядки (рядки-форм усі-рядки))

(визначити механізм-раст
  (функція (назва)
    (за-умовою
      ((однакові? назва (як-є lambda))
       "NecessaryFormMechanism::Lambda")
      ((однакові? назва (як-є define))
       "NecessaryFormMechanism::Define")
      ((атом? (як-є ())) (перше (як-є ()))))))

(визначити подати-рядок
  (функція (рядок)
    (нехай ((механізм (механізм-раст (форма-рядка рядок))))
      (за-умовою
        ((атом? механізм)
         (перше (як-є ())))
        ((атом? (як-є ()))
         (зчепити-рядки
           "    NecessaryFormDispatchRow { semantic_id: 0b"
           (значення-у-текст (перше рядок))
           ", mechanism: "
           механізм
           " },\n"))))))

(визначити подати-рядки
  (функція (залишок)
    (за-умовою
      ((атом? залишок)
       "")
      ((атом? (як-є ()))
       (зчепити-рядки (подати-рядок (перше залишок))
             (подати-рядки (решта залишок)))))))

(визначити заголовок
  (зчепити-рядки
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/surface/function-signatures.lisp\n"
    "// Generator: scripts/generate-rust-evaluator-dispatch.lisp\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) enum NecessaryFormMechanism {\n"
    "    Define,\n"
    "    Lambda,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub(super) struct NecessaryFormDispatchRow {\n"
    "    pub(super) semantic_id: u8,\n"
    "    pub(super) mechanism: NecessaryFormMechanism,\n"
    "}\n\n"
    "pub(super) const NECESSARY_FORM_DISPATCH: &[NecessaryFormDispatchRow] = &[\n"))

(визначити згенерований-вміст
  (зчепити-рядки заголовок (подати-рядки рядки) "];\n"))

(за-умовою
  ((атом? *argv*)
   (друге
     (список
       (записати-файл шлях-результату згенерований-вміст)
       (друкувати "Rust evaluator dispatch projection written")))))
  ((11110111 (100 *argv*) "--check")
   (нехай ((поточний-вміст (читати-файл шлях-результату)))
     (за-умовою
       ((однакові? поточний-вміст згенерований-вміст)
        (друкувати "Rust evaluator dispatch projection is current"))
       ((атом? (як-є ()))
        (друге
          (список
            (друкувати "Rust evaluator dispatch projection is stale")
            (перше (як-є ()))))))))
  ((010 (001 ()))
   (друге
     (список
       (записати-файл шлях-результату згенерований-вміст)
       (друкувати "Rust evaluator dispatch projection written"))))
