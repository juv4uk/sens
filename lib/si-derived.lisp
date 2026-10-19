; Похідні сталі Міжнародної системи одиниць SI.
;
; Джерело визначальних величин — lib/si.lisp, сім точних значень BIPM.
; Жодне значення тут не дублюється десятковим наближенням: кожна похідна
; стала обчислюється із відповідних визначальних величин чинною арифметикою
; SENS D5: «помножити» та «частка». Число 2 — звичайний людський десятковий
; операнд D24+, а фізичне кодування належить Zig/T5M.
;
; Імена si:... — наявні публічні ідентифікатори фізичних величин, якими
; користуються споживачі. Вони не є викличними головами / кодами доменів.
; Виконувані голови всіх семи форм — ратифіковані «визначити» (D4),
; «помножити» та «частка» (D5), у повній українській проєкції.
;
; Тут немає SID8, Sens8, історичного декодера, числових містків, макросів,
; дублюючих внутрішніх визначень чи залежності від зовнішнього evaluator.
;
; F = N_A · e — стала Фарадея.
(визначити si:faraday-constant
  (помножити
    si:avogadro-constant
    si:elementary-charge))

; R = N_A · k_B — молярна газова стала.
(визначити si:molar-gas-constant
  (помножити
    si:avogadro-constant
    si:boltzmann-constant))

; K_J = (2 · e) / h — стала Джозефсона.
(визначити si:josephson-constant
  (частка
    (помножити 2 si:elementary-charge)
    si:planck-constant))

; R_K = h / (e · e) — стала фон Клітцинга.
(визначити si:von-klitzing-constant
  (частка
    si:planck-constant
    (помножити si:elementary-charge si:elementary-charge)))

; Φ_0 = h / (2 · e) — квант магнітного потоку.
(визначити si:magnetic-flux-quantum
  (частка
    si:planck-constant
    (помножити 2 si:elementary-charge)))

; G_0 = (2 · e · e) / h — квант електричної провідності.
(визначити si:conductance-quantum
  (частка
    (помножити
      2
      (помножити si:elementary-charge si:elementary-charge))
    si:planck-constant))

; N_A · h — молярна стала Планка.
(визначити si:molar-planck-constant
  (помножити
    si:avogadro-constant
    si:planck-constant))
