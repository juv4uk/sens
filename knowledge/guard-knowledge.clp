; База знань охоронця драбин — у формі CLIPS (рушій правил).
;
; Навіщо: охоронець карає за дубль (правило), але його ЗНАННЯ про те, ЯК правити
; файли, лежало текстом у довіднику. Тут те саме знання виражено ФАКТАМИ й
; ПРАВИЛАМИ — у формі, яку розуміє рушій (crates/wsm-clips-kernel, lib/clips-import.lisp).
;
; Факт  = що є (гарячий файл, шар, клас помилки).
; Правило = що робити (якщо гарячий — прави маленькими кроками).
; Той, хто наповнює охоронця, додає ФАКТ або ПРАВИЛО, а не абзац прози.

(deftemplate guard-fact
  (slot kind)     ; hot-file | layer | error-class | projection
  (slot name)
  (slot value)
  (slot source))  ; звідки знання (коміт, довідник, урок)

(deffacts guard-knowledge
  (guard-fact (kind hot-file) (name "lib/core4.lisp") (value "634 змін / 23 дні") (source "guard-history-index"))
  (guard-fact (kind hot-file) (name "lib/core.lisp") (value "245 змін") (source "guard-history-index"))
  (guard-fact (kind layer) (name "x86-64 admission/encoding/lowering") (value "фізичний коридор") (source "урок 5"))
  (guard-fact (kind layer) (name "reason.lisp/forward.lisp") (value "опціональна проєкція #748") (source "урок 6"))
  (guard-fact (kind error-class) (name "ladder-shadowing") (value "дубль поверхні драбини") (source "охоронець --advise клас А")))

; УРОК 1: гарячий файл — малі кроки, не переписуй.
(defrule hot-file-small-steps
  (guard-fact (kind hot-file) (name ?f) (value ?v))
  =>
  (assert (guard-advice (file ?f) (advice "правити МАЛЕНЬКИМИ кроками, одне визначення")
                        (why ?v))))

; УРОК 3: не дублюй наявне — вжий драбину.
(defrule do-not-duplicate-ladder
  (guard-fact (kind error-class) (name "ladder-shadowing") (value ?v))
  =>
  (assert (guard-advice (file ?f) (advice "ужий наявну поверхню драбини") (why ?v))))

; УРОК 5: машина — окремий шар; перевіряй Zig, не Rust.
(defrule machine-layer-zig-tests
  (guard-fact (kind layer) (name ?n) (value "фізичний коридор"))
  =>
  (assert (guard-advice (file ?n) (advice "перевіряй Zig-тестами (ізоляція), не Rust")
                        (why "машина — окремий шар"))))

; Мета: (run) → усі поради виведено з фактів. Додав факт — отримав пораду.
