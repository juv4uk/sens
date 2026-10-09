; #432 research-only abstract fixed-point checker.
; This is NOT semantic authority and does not implement CAR/CDR.
;
; Declared lower basis B:
;   Canon 0, QUOTE, ATOM, EQ, CONS, COND, ordinary LAMBDA/DEFINE composition.
; Explicitly excluded:
;   CAR, CDR, peer-surface/registry round-trips, host pair destructuring,
;   backend loads, and any stronger hidden pair eliminator.
;
; The checker itself may use CAR/CDR to walk its research data structures.
; That meta-level convenience is not a candidate derivation in basis B.
;
; Abstract capability states:
;   static-atom      literal atom independent of runtime input
;   static-pair      pair containing no fresh runtime payload
;   fresh-nested     fresh runtime payload exists only inside a pair/structure
;   record-pair      ATOM/EQ structured observation record
;   undefined        route is not defined (for example EQ on pair data)
;   fresh-top-level  forbidden target: extracted runtime payload atom

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

; One abstract closure step for the declared lower basis.
;
; QUOTE contributes static-atom/static-pair (already seeded).
; ATOM maps every defined input class to a structured record => record-pair.
; EQ on non-pairs yields a structured record; on pair data it is undefined.
; CONS creates a pair; if an operand carries fresh payload, freshness remains nested.
; COND returns one branch value and therefore adds no capability absent in branches.
; LAMBDA/DEFINE bind/compose existing values and add no projection capability.
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
