% 1971 STRIPS positive finite action theory, 2026-10-09 D10 RESEARCH ONLY.
% SWI-Prolog independent oracle: enumerate ALL initial worlds and intersect
% those that satisfy the desired goal AFTER the given action. Not a SENS
% program, not an opcode, not an automatic Core selection.
:- use_module(library(ordsets)).
:- use_module(library(plunit)).
:- use_module(library(lists)).
:- use_module(library(apply)).

world_subseq([], []).
world_subseq([X|Xs], [X|Ys]) :- world_subseq(Xs, Ys).
world_subseq([_|Xs], Ys) :- world_subseq(Xs, Ys).

reaches(State, Pre, Adds, Deletes, Goal) :-
    ord_subset(Pre, State),
    ord_subtract(State, Deletes, Survived),
    ord_union(Survived, Adds, Next),
    ord_subset(Goal, Next).

intersect_successes([First|Rest], R) :-
    foldl(ord_intersection, Rest, First, R).

% Explicit finite closed universe is itself a research input.
oracle(Universe0, Pre0, Adds0, Deletes0, Goal0, Outcome) :-
    sort(Universe0, Universe),
    sort(Pre0, Pre), sort(Adds0, Adds),
    sort(Deletes0, Deletes), sort(Goal0, Goal),
    ord_intersection(Adds, Deletes, Ambiguous),
    Ambiguous == [],
    ord_union(Pre, Adds, PU),
    ord_union(PU, Deletes, PUD),
    ord_union(PUD, Goal, Relevant),
    ord_subset(Relevant, Universe),
    findall(S,
            (world_subseq(Universe, S), reaches(S, Pre, Adds, Deletes, Goal)),
            Successful),
    (Successful == [] ->
        Outcome = impossible
    ;   intersect_successes(Successful, Weakest),
        Outcome = required(Weakest)
    ).

% A second local symbolic interpretation checks the Prolog oracle's
% expected answers, but the oracle itself never uses this formula.
symbolic(Pre, Adds, Deletes, Goal, Outcome) :-
    ord_intersection(Goal, Deletes, Destroyed),
    (Destroyed \== [] ->
        Outcome = impossible
    ;   ord_subtract(Goal, Adds, Remaining),
        ord_union(Pre, Remaining, Required),
        Outcome = required(Required)
    ).

effect_split([], [], []).
effect_split([X|Xs], [X|Add], Del) :- effect_split(Xs, Add, Del).
effect_split([_|Xs], Add, Del) :- effect_split(Xs, Add, Del).
effect_split([X|Xs], Add, [X|Del]) :- effect_split(Xs, Add, Del).

:- begin_tests(d10_strips_goal_regression).

test(action_precondition_survives, true(R == required([ready]))) :-
    oracle([ready, observed], [ready], [observed], [], [observed], R).

test(vacuous_predecessor_is_possible_not_impossible, true(R == required([]))) :-
    oracle([ready, observed], [], [observed], [], [observed], R).

test(destructive_goal_is_not_empty_precondition, true(R == impossible)) :-
    oracle([observed], [], [], [observed], [observed], R).

test(irrelevant_delete, true(R == required([ready, retained]))) :-
    oracle([ready, observed, obsolete, retained], [ready],
           [observed], [obsolete], [observed, retained], R).

test(empty_goal_with_precondition, true(R == required([ready]))) :-
    oracle([ready], [ready], [ready], [], [], R).

test(empty_goal_no_precondition, true(R == required([]))) :-
    oracle([], [], [], [], [], R).

test(delete_own_precondition_after_use, true(R == required([ready]))) :-
    oracle([ready, observed], [ready], [observed], [ready], [observed], R).

test(another_required_goal_destroyed, true(R == impossible)) :-
    oracle([ready, observed], [], [observed], [ready],
           [ready, observed], R).

test(positive_requirement_witness_is_not_actionless) :-
    oracle([ready, observed], [ready], [observed], [],
           [observed], required([ready])),
    \+ reaches([], [ready], [observed], [], [observed]).

test(all_1728_bounded_action_goal_patterns_have_same_truth_table_result) :-
    U = [a, b, c],
    findall(1,
      (world_subseq(U, Pre),
       world_subseq(U, Goal),
       effect_split(U, Add, Delete),
       oracle(U, Pre, Add, Delete, Goal, Brute),
       symbolic(Pre, Add, Delete, Goal, Prediction),
       assertion(Brute == Prediction)),
      Results),
    length(Results, 1728).

:- end_tests(d10_strips_goal_regression).

main :-
    (run_tests([d10_strips_goal_regression]) ->
        writeln('D10 STRIPS SWI-Prolog independent 1728 worlds PASS; selected=0, ratified=0')
    ;   halt(1)
    ).
