:- initialization(main, main).

must(Goal, Label) :-
    (call(Goal) -> true ; throw(error(failed_subsumption_witness(Label),_))).
must_not(Goal, Label) :-
    (call(Goal) -> throw(error(incorrect_positive_subsumption(Label),_));true).

main :-
    % SWI-Prolog built-in subsumes_term/2 is read-only and one-sided.
    must(subsumes_term(f(X,X),f(a,a)), repeated_generic_var_same_atom),
    must(var(X), generic_variable_unbound_after_success),
    must_not(subsumes_term(f(Y,Y),f(a,b)), repeated_generic_var_mismatch),
    must(var(Y), generic_variable_unbound_after_failure),
    must(subsumes_term(f(Z,Z),f(S,S)), same_specific_variable_identity),
    must(var(Z), generic_remains_unbound_on_non_ground),
    must(var(S), specific_remains_unbound_on_non_ground),
    must_not(subsumes_term(f(A,A),f(T,b)), different_specific_var_and_atom),
    must(var(A), generic_remains_unbound_on_failure),
    must(var(T), specific_never_bound_to_b),
    must_not(subsumes_term(f(a,B),f(C,b)), one_sided_refuses_specific_binding),
    must(unifiable(f(a,B),f(C,b),_), unlike_symmetric_unification),
    must(var(B), generic_still_unbound),
    must(var(C), target_still_unbound),
    must(subsumes_term(f(D,g(D)),f(a,g(a))), nested_repeated_variable),
    must_not(subsumes_term(f(E,g(E)),f(a,g(b))), nested_mismatch),
    must(subsumes_term(f(F,G),f(H,H)), independent_generic_vars_may_share_target),
    must(var(F), generic_var_one_unbound),
    must(var(G), generic_var_two_unbound),
    must(var(H), specific_shared_var_unbound),
    must_not(subsumes_term(f(a),f(a,b)), arity_is_part_of_constructor),
    must_not(subsumes_term(f(a),g(a)), name_is_part_of_constructor),
    must(subsumes_term(parent(P,leo),parent(ann,leo)), advice_taker_rule_filter),
    must(var(P), observation_generic_unbound),
    must(subsumes_term(observation(sensor,State),observation(sensor,clear)), astronomy_schema),
    must(var(State), source_rule_unchanged),
    % Corpus is separate from 576-case Python subtree enumeration oracle.
    findall(1,
      (member(Pat,[a,b, f(_),f(a), f(X1,X1), f(_,_), p(a,_), p(_,_), p(A1,A1)]),
       member(Example,[a,b, f(a), f(b), f(a,a), f(a,b),f(_,_),p(a,a),p(a,b),p(b,b)]),
       (subsumes_term(Pat,Example)->true;true)),
       Checked),
    length(Checked,90),
    format("D10 SYMBOLIC AI SWI subsumes_term PASS finite witness probes=90 plus explicit asymmetric and non-binding cases~n").
