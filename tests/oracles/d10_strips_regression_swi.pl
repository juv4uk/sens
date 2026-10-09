% External SWI-Prolog donor executable. Research-only: NOT binary SENS.
% Historical lineage: Fikes & Nilsson, STRIPS (1971), positive ground
% add/delete planning; goal-regression law formalized in planning literature.
:- use_module(library(ordsets)).
:- use_module(library(lists)).
:- initialization(main, main).

canonical_set(L) :-
    is_list(L),
    maplist(atom, L),
    sort(L, L).

valid_operator(op(Pre, Add, Del)) :-
    canonical_set(Pre),
    canonical_set(Add),
    canonical_set(Del),
    ord_intersection(Add, Del, []).

progress(State, Operator, Result) :-
    canonical_set(State),
    valid_operator(Operator),
    Operator = op(Pre, Add, Del),
    ord_subset(Pre, State),
    ord_subtract(State, Del, Retained),
    ord_union(Retained, Add, Result).

% Regression is a logical weakest positive precondition; no requirement
% that the action must achieve some new goal (that is a search heuristic).
regress(Goal, Operator, PreviousGoal) :-
    canonical_set(Goal),
    valid_operator(Operator),
    Operator = op(Pre, Add, Del),
    ord_subtract(Goal, Add, Unachieved),
    ord_intersection(Unachieved, Del, []),
    ord_union(Pre, Unachieved, PreviousGoal).

witness(ID, Query) :-
    ( once(call(Query)) ->
        format("OBS\t~w\tPASS~n", [ID])
    ; throw(error(strips_contract_failed(ID), witness/2))
    ).

subset_of([], []).
subset_of([X|Xs], [X|Ys]) :- subset_of(Xs, Ys).
subset_of([_|Xs], Ys) :- subset_of(Xs, Ys).

bool(Goal, yes) :- once(Goal), !.
bool(_, no).

same_regression_semantics(State, Pre, Add, Del, Goal) :-
    Op = op(Pre, Add, Del),
    bool((progress(State, Op, Post), ord_subset(Goal, Post)), Forward),
    bool((regress(Goal, Op, Need), ord_subset(Need, State)), Backward),
    Forward == Backward.

all_small_ground_models(Count) :-
    findall(X, subset_of([a,b,c], X), Sets),
    findall(ok,
        ( member(State, Sets),
          member(Goal, Sets),
          member(Pre, Sets),
          member(Add, Sets),
          member(Del, Sets),
          valid_operator(op(Pre, Add, Del)),
          same_regression_semantics(State, Pre, Add, Del, Goal)
        ), Results),
    length(Results, Count),
    Count =:= 13824.

main :-
    witness(persists_frame,
      (progress([charged,old,safe], op([charged],[observed],[old]), [charged,observed,safe]))),
    witness(regresses_frame,
      (regress([observed,safe], op([charged],[observed],[old]), [charged,safe]))),
    witness(delete_conflict,
      (\+ regress([safe], op([],[],[safe]), _))),
    witness(relevant_add,
      (regress([observed], op([charged],[observed],[]), [charged]))),
    witness(irrelevant_but_sound,
      (regress([safe], op([charged],[observed],[]), [charged,safe]))),
    witness(no_forced_action_usefulness,
      (regress([safe], op([],[],[]), [safe]))),
    witness(precondition_must_hold,
      (\+ progress([safe], op([charged],[observed],[]), _))),
    witness(goal_not_precondition,
      (regress([observed], op([charged],[observed],[]), [charged]))),
    witness(before_preconditions,
      (regress([safe], op([charged],[],[]), [charged,safe]))),
    witness(empty_goal_requires_preconditions,
      (regress([], op([charged],[observed],[]), [charged]))),
    witness(empty_preconditions,
      (regress([], op([],[],[]), []))),
    witness(add_del_disjoint_required,
      (\+ valid_operator(op([],[a],[a])))),
    witness(unsorted_set_rejected,
      (\+ valid_operator(op([b,a],[],[])))),
    witness(duplicate_set_rejected,
      (\+ valid_operator(op([a,a],[],[])))),
    witness(variable_symbol_rejected,
      (\+ valid_operator(op([_],[],[])))),
    witness(nonatom_term_rejected,
      (\+ valid_operator(op([f(a)],[],[])))),
    witness(non_ground_goal_rejected,
      (\+ regress([_],op([],[],[]),_))),
    witness(delete_list_does_not_mean_negated_precondition,
      (progress([a,b],op([a],[],[b]),[a]))),
    witness(negative_goal_is_out_of_scope,
      (\+ regress([not(a)],op([],[],[]),_))),
    witness(two_step_plan_backwards,
      (regress([at_c], op([at_b],[at_c],[at_b]), [at_b]),
       regress([at_b],op([at_a],[at_b],[at_a]),[at_a]))),
    witness(two_step_plan_forwards,
      (progress([at_a],op([at_a],[at_b],[at_a]),[at_b]),
       progress([at_b],op([at_b],[at_c],[at_b]),[at_c]))),
    witness(impossible_goal_even_with_precondition,
      (\+ regress([a],op([a],[],[a]),_))),
    witness(independent_goal_survives,
      (regress([safe],op([charged],[charged],[old]),[charged,safe]))),
    witness(exhaustive_forward_backward_equivalence,
      all_small_ground_models(13824)),
    format("STRIPS-SUMMARY\tSWI-PROLOG\t24\tEXHAUSTIVE-13824~n", []),
    halt(0).
