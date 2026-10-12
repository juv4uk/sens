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

(0011 guard-fact-field (0010 (field fact) ((0010 (pair) (110 ((010 pair) () (001 ()))
                                                                                        ((010 pair) (1) (001 ())) (t (1001 pair)))) (11100 field (011 fact)))))
(0011 guard-fact-state-field (0010 (field state) ((0010 (pair) (110 ((010 pair) () (001 ()))
                                                                                          ((010 pair) (1) (001 ())) (t (1001 pair)))) (11100 field state))))
(0011 guard-fact-evaluate (0010 (fact) ((0010 (source subject state) (110 ((101 source (001 git)) ((0010 (head dirty) (110 ((101 dirty (001 clean)) (make-guard-finding (001 allow) (001 confirmed) subject (001 git) (001 working-tree-clean) (001 uncommitted-changes-absent) (001 no-action-required) (001 continue) (1110 (001 head) head))) ((101 dirty (001 dirty)) (make-guard-finding (001 warn) (001 confirmed) subject (001 git) (001 working-tree-must-be-explainable) (1110 (001 expected) (001 clean) (001 observed) (001 dirty)) (001 explanation-or-commit-required) (001 inspect-and-explain-every-change) (1110 (001 head) head))) ((010 (001 ())) (guard-unknown subject (001 unclassifiable-git-state) (001 choose-unknown-route))))) (guard-fact-state-field (001 head) state) (guard-fact-state-field (001 dirty) state))) ((101 source (001 systemd)) ((0010 (active) (110 ((101 active (001 active)) (make-guard-finding (001 allow) (001 confirmed) subject (001 systemd) (001 service-running) (001 ()) (001 expected-state) (001 continue) (1110 (001 active) active))) ((101 active (001 inactive)) (make-guard-finding (001 warn) (001 confirmed) subject (001 systemd) (001 service-inactive-but-installed) (1110 (001 expected) (001 active) (001 observed) active) (001 service-not-running) (001 inspect-unit-and-start-if-required) (1110 (001 active) active))) ((010 (001 ())) (guard-unknown subject (001 unclassifiable-service-state) (001 choose-unknown-route))))) (guard-fact-state-field (001 active) state))) ((101 source (001 swarm)) ((0010 (lock identity) (110 ((101 identity (001 present)) (make-guard-finding (001 allow) (001 confirmed) subject (001 swarm) (001 identity-present) (001 identity-file-observed) (001 no-action-required) (001 continue) (1110 (001 lock) lock (001 identity) identity))) ((010 (001 ())) (guard-unknown subject (001 swarm-identity-not-observed) (001 choose-unknown-route))))) (guard-fact-state-field (001 lock) state) (guard-fact-state-field (001 identity) state))) ((010 (001 ())) (guard-unknown subject (001 unclassified-fact-source) (001 choose-unknown-route))))) (guard-fact-field (001 source) fact) (guard-fact-field (001 subject) fact) (guard-fact-field (001 state) fact))))
