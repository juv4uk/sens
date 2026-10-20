; #432 дослідницький абстрактний перевіряч нерухомої точки.
; Це НЕ семантична влада і не реалізує CAR/CDR.
;
; Оголошена нижня основа B:
;   Canon 0, QUOTE, ATOM, EQ, CONS, COND, звичайна композиція LAMBDA/DEFINE.
; Явно виключено:
;   CAR, CDR, round-trip peer-surface/реєстру, деструктуризацію пар хоста,
;   завантаження бекенда й будь-який сильніший прихований елімінатор пар.
;
; Сам перевіряч може вживати CAR/CDR для обходу своїх дослідницьких структур даних.
; Ця мета-рівнева зручність не є кандидатною деривацією в основі B.
;
; Абстрактні стани можливостей:
;   static-atom      літеральний атом, незалежний від вхідних даних часу виконання
;   static-pair      пара без свіжого корисного навантаження часу виконання
;   fresh-nested     свіже корисне навантаження часу виконання існує лише всередині пари/структури
;   record-pair      структурований запис спостереження ATOM/EQ
;   undefined        маршрут не визначено (наприклад EQ на даних пари)
;   fresh-top-level  заборонена ціль: витягнутий атом корисного навантаження часу виконання

(def research-same?
  (lambda (left right)
    (cond
      ((equal? left right) (structural-relation same) (quote yes))
      ((equal? left right) (structural-relation distinct) (quote no)))))

(def research-set-contains?
  (lambda (needle values)
    (cond
      ((atom values) (structural-kind empty-list) (quote no))
      ((atom values) (structural-kind pair)
       (cond
         ((research-same? needle (car values)) yes (quote yes))
         ((research-same? needle (car values)) no
          (research-set-contains? needle (cdr values)))))
      ((atom values) (structural-kind atom) (quote no)))))

(def research-set-add
  (lambda (value values)
    (cond
      ((research-set-contains? value values) yes values)
      ((research-set-contains? value values) no (cons value values)))))

; Один абстрактний крок замикання для оголошеної нижньої основи.
;
; QUOTE дає static-atom/static-pair (уже засіяні).
; ATOM відображає кожен визначений вхідний клас у структурований запис => record-pair.
; EQ на не-парах дає структурований запис; на даних пари він невизначений.
; CONS створює пару; якщо операнд несе свіже навантаження, свіжість лишається вкладеною.
; COND повертає одне значення гілки і тому не додає можливості, відсутньої в гілках.
; LAMBDA/DEFINE зв'язують/компонують наявні значення й не додають можливості проєкції.
(def research-transfer-step
  (lambda (states)
    (cond
      ((research-set-contains? (quote fresh-nested) states) yes
       (research-set-add
         (quote undefined)
         (research-set-add
           (quote record-pair)
           (research-set-add
             (quote static-pair)
             (research-set-add (quote fresh-nested) states)))))
      ((research-set-contains? (quote fresh-nested) states) no
       (research-set-add
         (quote undefined)
         (research-set-add
           (quote record-pair)
           (research-set-add (quote static-pair) states)))))))

(def research-result
  (lambda (status round states)
    (list
      (quote fresh-atom-search)
      (list (quote basis)
            (quote (canon-empty-list quote atom eq cons cond lambda define)))
      (list (quote excluded)
            (quote (car cdr peer-surface registry-roundtrip host-pair-destructure backend-load hidden-pair-eliminator)))
      (list (quote bound) 8)
      (list (quote stabilized-at) round)
      (list (quote reachable) states)
      (list (quote fresh-top-level)
            (cond
              ((research-set-contains? (quote fresh-top-level) states) yes (quote yes))
              ((research-set-contains? (quote fresh-top-level) states) no (quote no))))
      (list (quote result) status))))

(def research-search-next
  (lambda (remaining round states next)
    (cond
      ((research-set-contains? (quote fresh-top-level) next) yes
       (research-result (quote witness-found) round next))
      ((research-set-contains? (quote fresh-top-level) next) no
       (cond
         ((research-same? states next) yes
          (research-result (quote relative-no-projection-capability) round next))
         ((research-same? states next) no
          (cond
            ((eq remaining 0) (identity-relation same)
             (research-result (quote insufficient-bound) round next))
            ((eq remaining 0) (identity-relation distinct)
             (research-search-loop (- remaining 1) (+ round 1) next)))))))))

(def research-search-loop
  (lambda (remaining round states)
    (research-search-next remaining round states (research-transfer-step states))))

(research-search-loop 8 0 (quote (fresh-nested static-atom static-pair)))
