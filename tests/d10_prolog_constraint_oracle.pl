% D10 research only — real SWI-Prolog donor witnesses, NOT SENS semantics.
% Source: https://www.swi-prolog.org/pldoc/man?predicate=unify_with_occurs_check%2F2
%         https://www.swi-prolog.org/pldoc/man?predicate=dif%2F2
%         https://www.swi-prolog.org/pldoc/man?predicate=copy_term%2F3
% ISO occurrence-aware unification; SWI-specific attributed variable semantics.
% Print only stable machine-readable boolean evidence, never unbound variable ids.
:- use_module(library(dif)).

check(Name, Goal) :-
    ( catch(call(Goal), Error,
            ( print_message(error, Error), fail ))
    -> format('PASS|~w~n', [Name])
    ;  format(user_error, 'FAIL|~w~n', [Name]), halt(2)
    ).

occurs_ground_injective :-
    unify_with_occurs_check(f(X, a), f(b, Y)),
    X == b, Y == a.

occurs_sharing_preserved :-
    unify_with_occurs_check(pair(X, X), pair(z, Y)),
    X == z, Y == z.

occurs_rejects_new_cycle :-
    \+ unify_with_occurs_check(X, f(X)).

occurs_rejects_functor_mismatch :-
    \+ unify_with_occurs_check(f(a), g(a)).

dif_ground_distinct :-
    dif(a, b).

dif_delayed_survives_unbound :-
    dif(X, a),
    var(X),
    \+ (X = a),
    var(X).

dif_accepts_safe_binding :-
    dif(X, a), X = b, X == b.

dif_rejects_ground_equal :-
    \+ dif(a, a).

dif_prevents_delayed_equality :-
    \+ (dif(X, a), X = a).

copy_fresh_sharing :-
    copy_term(pair(X, X), pair(A, B), Goals),
    Goals == [],
    A == B,
    A \== X.

copy_restores_one_constraint :-
    dif(X, a),
    copy_term(X, Y, Goals),
    Goals \= [], var(Y),
    maplist(call, Goals),
    \+ (Y = a),
    Y = b.

copy_restores_two_constraints :-
    dif(X, a), dif(X, b),
    copy_term(X, Y, Goals),
    Goals \= [], var(Y),
    maplist(call, Goals),
    \+ (Y = a),
    \+ (Y = b),
    Y = c.

copy_without_residual_replay_allows_forbidden_value :-
    dif(X, a),
    copy_term(X, Y, Goals),
    Goals \= [], var(Y),
    % Deliberately do not call Goals: a fresh variable has no restored store.
    Y = a.

main :-
    current_prolog_flag(version_data, swi(Major, Minor, Patch, _)),
    format('SWI_VERSION|~d.~d.~d~n', [Major, Minor, Patch]),
    check('occurs-ground-injective', occurs_ground_injective),
    check('occurs-sharing-preserved', occurs_sharing_preserved),
    check('occurs-rejects-new-cycle', occurs_rejects_new_cycle),
    check('occurs-rejects-functor-mismatch', occurs_rejects_functor_mismatch),
    check('dif-ground-distinct', dif_ground_distinct),
    check('dif-delayed-survives-unbound', dif_delayed_survives_unbound),
    check('dif-accepts-safe-binding', dif_accepts_safe_binding),
    check('dif-rejects-ground-equal', dif_rejects_ground_equal),
    check('dif-prevents-delayed-equality', dif_prevents_delayed_equality),
    check('copy-fresh-sharing', copy_fresh_sharing),
    check('copy-restores-one-constraint', copy_restores_one_constraint),
    check('copy-restores-two-constraints', copy_restores_two_constraints),
    check('copy-without-residual-replay-allows-forbidden-value',
          copy_without_residual_replay_allows_forbidden_value).
