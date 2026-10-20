; Генератор проєкції диспетчеризації необхідних форм обчислювача.
; Джерело повноважень — lib/surface/function-signatures.lisp,
; поле (form ...) у рядку таблиці.
; Раст отримує лише механічний опис виконання, без нових законів СЕНС.
;
; Запуск:
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-evaluator-dispatch.lisp --check

(визначити шлях-джерела "lib/surface/function-signatures.lisp")
(визначити шлях-виходу "crates/sens/src/eval/necessary_forms_generated.rs")

(визначити рядок+
  (функція аргументи
    (згорнути (функція (накопичувач с) (рядок-додати накопичувач с)) "" аргументи)))

;; Особливі форми вибираємо за полем даних (form lambda|define).
;; Значення lambda і define у цьому полі — дані, а не виклики.
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
      (так
       (за-умовою
         ((атом? (знайти-за-ключем (як-є form) (решта (перше залишок))))
          (рядки-форм (решта залишок)))
         (так
          (сполучити (перше залишок) (рядки-форм (решта залишок)))))))))

(визначити рядки (рядки-форм усі-рядки))

(визначити механізм-для-русту
  (функція (назва)
    (за-умовою
      ((однакові? назва (як-є lambda))
       "NecessaryFormMechanism::Lambda")
      ((однакові? назва (як-є define))
       "NecessaryFormMechanism::Define")
      (так (перше (як-є ()))))))

(визначити відрендерити-рядок
  (функція (рядок)
    (нехай ((механізм (механізм-для-русту (форма-рядка рядок))))
      (за-умовою
        ((атом? механізм)
         (перше (як-є ())))
        (так
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
      (так
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

; Рядки результату та параметр --check належать інтерфейсу Раст.
(за-умовою
  ((атом? *argv*)
   (друге
     (список
       (записати-файл шлях-виходу згенероване)
       (друкувати "Rust evaluator dispatch projection written"))))
  ((однакові? (перше *argv*) "--check")
   (нехай ((поточне (читати-файл шлях-виходу)))
     (за-умовою
       ((однакові? поточне згенероване)
        (друкувати "Rust evaluator dispatch projection is current"))
       (так
        (друге
          (список
            (друкувати "Rust evaluator dispatch projection is stale")
            (перше (як-є ()))))))))
  (так
   (друге
     (список
       (записати-файл шлях-виходу згенероване)
       (друкувати "Rust evaluator dispatch projection written")))))
