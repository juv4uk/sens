% (role research-only)
% (semantic-authority-change none)
% Independent finite propositional abductive oracle.
% This is a test model, not a historical SWI-Prolog abductive API and not SENS.
:- initialization(main, main).

% case(Id, Facts, Rules, Abducibles, ForbiddenConjunctions, Goal).
case(wet_shoes_two_minima, [],
     [rule(wet_shoes,[rain]), rule(wet_shoes,[sprinkler])],
     [rain,sprinkler], [], wet_shoes).

case(empty_explanation_is_success, [sunlight],
     [rule(plant_ready,[sunlight])],
     [rain,sprinkler], [], plant_ready).

case(no_explanation_is_not_empty_success, [], [],
     [rain,sprinkler], [], mystery).

case(integrity_constraint_filters_explanation, [moon],
     [rule(wet_shoes,[rain]), rule(wet_shoes,[sprinkler])],
     [rain,sprinkler], [[rain,moon]], wet_shoes).

case(conjunction_keeps_all_required_abducibles, [],
     [rule(alarm,[power,smoke])],
     [noise,power,smoke], [], alarm).

case(unsupported_cycle_does_not_self_prove, [],
     [rule(p,[q]), rule(q,[p])],
     [], [], p).

case(seeded_cycle_reaches_fixpoint, [],
     [rule(p,[q]), rule(q,[p]), rule(q,[seed])],
     [seed], [], p).

case(integrity_checks_derived_closure, [],
     [rule(wet_shoes,[rain]), rule(danger,[rain]), rule(wet_shoes,[sprinkler])],
     [rain,sprinkler], [[danger]], wet_shoes).

case(canonical_output_ignores_input_order, [],
     [rule(wet_shoes,[sprinkler]), rule(wet_shoes,[rain])],
     [sprinkler,rain], [], wet_shoes).

case(duplicate_rules_do_not_duplicate_explanations, [],
     [rule(wet_shoes,[rain]), rule(wet_shoes,[rain])],
     [rain], [], wet_shoes).

case(non_abducible_atoms_cannot_be_hypothesized, [],
     [rule(target,[unlisted_atom])],
     [rain], [], target).

case(mixed_size_minimal_explanations_order_by_size, [],
     [rule(goal,[rain]), rule(goal,[power,smoke])],
     [smoke,rain,power], [], goal).

powerset([], [[]]).
powerset([Head|Tail], Sets) :-
    powerset(Tail, WithoutHead),
    prepend_to_each(Head, WithoutHead, WithHead),
    append(WithoutHead, WithHead, Sets).

prepend_to_each(_, [], []).
prepend_to_each(Head, [Set|Sets], [[Head|Set]|Rest]) :-
    prepend_to_each(Head, Sets, Rest).

subset_of([], _).
subset_of([Head|Tail], Set) :-
    memberchk(Head, Set),
    subset_of(Tail, Set).

closure(Facts, Rules, Explanation, Result) :-
    append(Facts, Explanation, Seed0),
    sort(Seed0, Seed),
    closure_step(Seed, Rules, Result).

closure_step(Current, Rules, Result) :-
    findall(Head,
            ( member(rule(Head, Body), Rules),
              subset_of(Body, Current),
              \+ memberchk(Head, Current)
            ),
            New0),
    sort(New0, New),
    ( New = []
    -> Result = Current
    ;  append(Current, New, Extended),
       sort(Extended, Next),
       closure_step(Next, Rules, Result)
    ).

coherent(Closure, Constraints) :-
    \+ ( member(Forbidden, Constraints),
         subset_of(Forbidden, Closure)
       ).

strict_subset(Left, Right) :-
    Left \== Right,
    subset_of(Left, Right).

compare_explanation(Order, Left, Right) :-
    length(Left, LeftSize),
    length(Right, RightSize),
    ( LeftSize < RightSize
    -> Order = '<'
    ; LeftSize > RightSize
    -> Order = '>'
    ; compare(Order, Left, Right)
    ).

solve(Facts, Rules, Abducibles, Constraints, Goal, Answers) :-
    sort(Abducibles, CanonicalAbducibles),
    powerset(CanonicalAbducibles, Candidates),
    findall(Explanation,
            ( member(Explanation, Candidates),
              closure(Facts, Rules, Explanation, Derived),
              memberchk(Goal, Derived),
              coherent(Derived, Constraints)
            ),
            Eligible0),
    sort(Eligible0, Eligible),
    findall(Explanation,
            ( member(Explanation, Eligible),
              \+ ( member(Sub, Eligible),
                   strict_subset(Sub, Explanation)
                 )
            ),
            Minimal0),
    sort(Minimal0, MinimalUnique),
    predsort(compare_explanation, MinimalUnique, Answers).

write_explanations([]) :- write('NONE').
write_explanations([Explanation|Rest]) :-
    write_explanation(Explanation),
    write_more_explanations(Rest).

write_more_explanations([]).
write_more_explanations([Explanation|Rest]) :-
    write(';'),
    write_explanation(Explanation),
    write_more_explanations(Rest).

write_explanation([]) :- write('EPS').
write_explanation([Atom|Rest]) :-
    write(Atom),
    write_comma_atoms(Rest).

write_comma_atoms([]).
write_comma_atoms([Atom|Rest]) :-
    write(','),
    write(Atom),
    write_comma_atoms(Rest).

run_case(Id) :-
    case(Id, Facts, Rules, Abducibles, Constraints, Goal),
    solve(Facts, Rules, Abducibles, Constraints, Goal, Answers),
    write('RESULT|'),
    write(Id),
    write('|'),
    write_explanations(Answers),
    nl.

main :-
    forall(case(Id, _, _, _, _, _), run_case(Id)).
