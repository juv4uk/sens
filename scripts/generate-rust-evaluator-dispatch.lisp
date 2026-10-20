; Lisp-owned generator for the evaluator necessary-form dispatch projection.
;
; Authority: lib/surface/function-signatures.lisp (поле (form ...) рядка таблиці)
; Rust receives only a mechanical execution projection.
;
; Usage:
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(визначити шлях-джерела "lib/surface/function-signatures.lisp")
(визначити шлях-виходу "crates/sens/src/eval/necessary_forms_generated.rs")

(визначити рядок+
  (функція аргументи
    (згорнути (функція (накопичувач с) (рядок-додати накопичувач с)) "" аргументи)))

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

(визначити механізм-для-русту
  (функція (назва)
    (за-умовою
      ((однакові? назва (як-є lambda))
       "NecessaryFormMechanism::Lambda")
      ((однакові? назва (як-є define))
       "NecessaryFormMechanism::Define")
      ((атом? (як-є ())) (перше (як-є ()))))))

(визначити відрендерити-рядок
  (функція (рядок)
    (нехай ((механізм (механізм-для-русту (форма-рядка рядок))))
      (за-умовою
        ((атом? механізм)
         (перше (як-є ())))
        ((атом? (як-є ()))
         (рядок+
           "    NecessaryFormDispatchRow { semantic_id: 0b"
           (значення-у-текст (перше рядок))
           ", mechanism: "
           механізм
           " },\n"))))))

(визначити відрендерити-рядки
  (функція (залишок)
    (за-умовою
      ((атом? залишок)
       "")
      ((атом? (як-є ()))
       (рядок+ (відрендерити-рядок (перше залишок))
             (відрендерити-рядки (решта залишок)))))))

(визначити заголовок
  (рядок+
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

(визначити згенероване
  (рядок+ заголовок (відрендерити-рядки рядки) "];\n"))

(за-умовою
  ((атом? *argv*)
   (друге
     (список
       (записати-файл шлях-виходу згенероване)
       (друкувати "Rust evaluator dispatch projection written")))))
  ((однакові? (перше *argv*) "--check")
   (нехай ((поточне (читати-файл шлях-виходу)))
     (за-умовою
       ((однакові? поточне згенероване)
        (друкувати "Rust evaluator dispatch projection is current"))
       ((атом? (як-є ()))
        (друге
          (список
            (друкувати "Rust evaluator dispatch projection is stale")
            (перше (як-є ()))))))))
  ((атом? (як-є ()))
   (друге
     (список
       (записати-файл шлях-виходу згенероване)
       (друкувати "Rust evaluator dispatch projection written"))))
