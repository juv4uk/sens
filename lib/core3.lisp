; #1134 — Core3 experimental kernel profile.
;
; This profile is intentionally thin. The selector and mechanism metadata are
; shared language-owned facilities; Core3 must not fork or duplicate them.
;
; Load order:
;   lib/core4.lisp (current runtime substrate for these profile tools)
;   lib/surface/semantic-registry-api.lisp
;   lib/mechanism-selector.lisp
;   lib/core3.lisp
;
; Core3 does not turn native kernel observations into global language truth.

; D3 owns the four-item proper list; no host QUOTE-list constructor.
; The order and empty tail are checked by binary SENS, not Python/Rust laws.
(визначити ядро3-виконавці
  (сполучити (як-є common-lisp)
    (сполучити (як-є prolog)
      (сполучити (як-є clips)
        (сполучити (як-є datalog)
          (як-є ()))))))

(визначити ядро3-маршрут
  (функція (ідентичність виконавець)
    (вибрати-механізм ідентичність виконавець)))

(визначити ядро3-додати-маршрути
  (функція (ідентичність)
    (список
      (ядро3-маршрут ідентичність (як-є common-lisp))
      (ядро3-маршрут ідентичність (як-є prolog))
      (ядро3-маршрут ідентичність (як-є clips))
      (ядро3-маршрут ідентичність (як-є datalog)))))

(визначити ядро3-стан-профілю
  (функція ()
    (як-є
      (core3
        (contract 7 0)
        (role experimental-kernel-laboratory)
        (selector shared-lisp-owned)
        (lowering partial)
        (clips-result-observation blocked)
        (four-island-round-trip pending)))))