% Foreign SWI-Prolog research oracle, not executable SENS source.
% (role research-only) (semantic-authority-change none)
% Primary manual: https://www.swi-prolog.org/pldoc/man?predicate=term_subsumer%2F3
:- use_module(library(terms)).
:- use_module(library(plunit)).
:- begin_tests(d10_finite_ground_anti_unify).

test(identical_ground_atom) :-
    term_subsumer(a, a, Result), Result == a.

test(different_ground_atoms) :-
    term_subsumer(a, b, Result), var(Result).

test(incompatible_functors) :-
    term_subsumer(f(a), g(a), Result), var(Result).

test(matching_functor_preserved) :-
    term_subsumer(f(a, b), f(a, c), General),
    General = f(a, Hole), var(Hole),
    subsumes_term(General, f(a, b)),
    subsumes_term(General, f(a, c)).

test(same_ordered_pair_shares_variable) :-
    term_subsumer(f(a, a), f(b, b), General),
    General = f(First, Second), var(First), First == Second,
    subsumes_term(General, f(a, a)),
    subsumes_term(General, f(b, b)).

test(different_pairs_not_shared) :-
    term_subsumer(f(a, a), f(b, c), General),
    General = f(First, Second), var(First), var(Second), First \== Second,
    subsumes_term(General, f(a, a)),
    subsumes_term(General, f(b, c)).

test(deep_sharing_preserved) :-
    term_subsumer(f(g(a), g(a)), f(g(b), g(b)), General),
    General = f(g(First), g(Second)), First == Second.

test(deep_different_pairs) :-
    term_subsumer(f(g(a), g(c)), f(g(b), g(d)), General),
    General = f(g(First), g(Second)), First \== Second.

test(all_matching_preserved) :-
    term_subsumer(f(a, a), f(a, a), General),
    General == f(a, a).

test(reversed_arguments_generalization) :-
    term_subsumer(f(a, b), f(c, d), First),
    term_subsumer(f(c, d), f(a, b), Second),
    First =@= Second.

test(ground_integer_disagreement_shares) :-
    term_subsumer(p(1, 1), p(2, 2), General),
    General = p(First, Second), First == Second.

test(ground_integer_distinct_disagreements) :-
    term_subsumer(p(1, 2), p(2, 1), General),
    General = p(First, Second), First \== Second.

test(different_arities_make_variable) :-
    term_subsumer(f(a), f(a, b), General), var(General).

test(most_specific_not_just_any_generalization) :-
    term_subsumer(k(x, g(a), g(a)), k(x, g(b), g(b)), General),
    General = k(x, g(V1), g(V2)),
    V1 == V2,
    General \=@= k(_, _, _),
    subsumes_term(General, k(x, g(a), g(a))),
    subsumes_term(General, k(x, g(b), g(b))).

:- end_tests(d10_finite_ground_anti_unify).
