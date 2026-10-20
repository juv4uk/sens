; #215 EMPTY-LIST-STRUCTURE-1 — свідки переходу Canon 0, що належать Lisp.
; Очікувані семантичні результати живуть тут. Rust може лише транспортувати фактичні результати
; до tests/fixtures/witness-runner.lisp для порівняння.
;
; Рядки ACTIVE доводять ранню структурну половину #215 уже тепер:
;   * () лишається звичайними даними порожнього списку й термінатором правильного списку;
;   * структурний порожній і числовий нуль лишаються спостережувано різними значеннями.
;
; Рядки BLOCKED зберігають уже доведену RED-ціль для фінальної половини:
;   * вироблення () не повинно споживатися потоком контролю як бінарний FALSE.
; Вони навмисно не активні, доки #218 не дасть структурним спостереженням
; явну алгебру результатів, а #217 не дасть контролю явний протокол рішень.
; Ми не додаємо прихованого режиму bootstrap/legacy-cond, бо семантика не повинна
; залежати від контексту завантажувача.
;
; Покриття нуль-відповіді багатого міркування належить #219; #215 лишається відкритим, доки
; не буде присутній міждоменний свідок і не зможуть активуватися заблоковані рядки контролю.

((expr . "(quote ())")
 (expected . "()")
 (owner . canon-zero)
 (active . t)
 (note . "Canon 0 materializes as the empty list, not a truth sentinel"))

((expr . "(cdr (quote (ground)))")
 (expected . "()")
 (owner . canon-zero)
 (active . t)
 (note . "proper-list termination still produces the same structural empty list"))

((expr . "(cons (quote ()) (cons 0/1 (quote ())))")
 (expected . "(() 0)")
 (owner . canon-zero)
 (active . t)
 (note . "empty-list data and exact numeric zero remain distinct list elements"))

((expr . "(cond (() (quote forbidden)) (t (quote legacy-false)))")
 (error . "Type")
 (owner . canon-zero)
 (blocked-by . control-logic-217)
 (depends-on . structural-observation-218)
 (note . "RED proven in PR #235: literal empty list must eventually be rejected as a decision, but activating this before #218/#217 breaks Lisp bootstrap"))

((expr . "(cond ((cdr (quote (ground))) (quote forbidden)) (t (quote legacy-false)))")
 (error . "Type")
 (owner . canon-zero)
 (blocked-by . control-logic-217)
 (depends-on . structural-observation-218)
 (note . "RED proven in PR #235: an operation producing () must not become FALSE; retained as future executable target"))
