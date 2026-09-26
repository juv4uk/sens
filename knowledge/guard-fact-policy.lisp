; Runtime fact policy for the wsm-guard-facts adapter (G2 slice).
; Runtime-політика фактів для адаптера wsm-guard-facts (G2 зріз).
;
; wsm-guard-facts normalizes read-only Git/systemd/swarm observations into
; `(fact (source S) (subject X) (state ...))` clauses. This policy owns the
; classification decision. Missing or unobservable evidence stays UNKNOWN via
; guard-unknown - never an implicit reject.
;
; wsm-guard-facts нормалізує read-only спостереження Git/systemd/swarm у
; `(fact (source S) (subject X) (state ...))` clause. Ця політика визначає
; класифікацію. Відсутній або неспостережуваний доказ лишається UNKNOWN через
; guard-unknown - ніколи не перетворюється на неявний reject.

(def guard-fact-field (lambda (field fact) (let ((pair (assoc field (cdr fact)))) (cond ((atom? pair) () (quote ()))
                                                                                        ((atom? pair) (1) (quote ())) (t (second pair))))))
(def guard-fact-state-field (lambda (field state) (let ((pair (assoc field state))) (cond ((atom? pair) () (quote ()))
                                                                                          ((atom? pair) (1) (quote ())) (t (second pair))))))
(def guard-fact-evaluate (lambda (fact) (let ((source (guard-fact-field (quote source) fact)) (subject (guard-fact-field (quote subject) fact)) (state (guard-fact-field (quote state) fact))) (cond ((eq? source (quote git)) (let ((head (guard-fact-state-field (quote head) state)) (dirty (guard-fact-state-field (quote dirty) state))) (cond ((eq? dirty (quote clean)) (make-guard-finding (quote allow) (quote confirmed) subject (quote git) (quote working-tree-clean) (quote uncommitted-changes-absent) (quote no-action-required) (quote continue) (list (quote head) head))) ((eq? dirty (quote dirty)) (make-guard-finding (quote warn) (quote confirmed) subject (quote git) (quote working-tree-must-be-explainable) (list (quote expected) (quote clean) (quote observed) (quote dirty)) (quote explanation-or-commit-required) (quote inspect-and-explain-every-change) (list (quote head) head))) (t (guard-unknown subject (quote unclassifiable-git-state) (quote choose-unknown-route)))))) ((eq? source (quote systemd)) (let ((active (guard-fact-state-field (quote active) state))) (cond ((eq? active (quote active)) (make-guard-finding (quote allow) (quote confirmed) subject (quote systemd) (quote service-running) (quote ()) (quote expected-state) (quote continue) (list (quote active) active))) ((eq? active (quote inactive)) (make-guard-finding (quote warn) (quote confirmed) subject (quote systemd) (quote service-inactive-but-installed) (list (quote expected) (quote active) (quote observed) active) (quote service-not-running) (quote inspect-unit-and-start-if-required) (list (quote active) active))) (t (guard-unknown subject (quote unclassifiable-service-state) (quote choose-unknown-route)))))) ((eq? source (quote swarm)) (let ((lock (guard-fact-state-field (quote lock) state)) (identity (guard-fact-state-field (quote identity) state))) (cond ((eq? identity (quote present)) (make-guard-finding (quote allow) (quote confirmed) subject (quote swarm) (quote identity-present) (quote identity-file-observed) (quote no-action-required) (quote continue) (list (quote lock) lock (quote identity) identity))) (t (guard-unknown subject (quote swarm-identity-not-observed) (quote choose-unknown-route)))))) (t (guard-unknown subject (quote unclassified-fact-source) (quote choose-unknown-route)))))))
