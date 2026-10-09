:- use_module(library(terms)).
:- initialization(main, main).

% Real SWI-Prolog donor: term_subsumer/3 is not the SENS runtime.
must(Goal, Label) :-
    ( call(Goal) -> true ; throw(error(failed_symbolic_ai_witness(Label), _)) ).

test_lgg(A, B, Expected, Label) :-
    term_subsumer(A, B, G),
    must((G =@= Expected), Label),
    must(subsumes_term(G, A), ground_instantiates_left),
    must(subsumes_term(G, B), ground_instantiates_right).

term_corpus(T) :-
    member(T, [a,b,c,f(a),f(b),f(c),g(a),g(b),
               pair(a,a),pair(a,b),pair(b,a),pair(b,b),
               pair(f(a),g(b)),pair(f(b),g(a)),
               pair(f(a),f(a)),pair(f(b),f(b)),
               t(a,b,c),t(a,a,b)]).

main :-
    X = _,
    test_lgg(pair(a,a), pair(b,b), pair(X,X), repeated_disagreement_identity),
    test_lgg(pair(a,a), pair(b,c), pair(_,_), distinct_disagreement_pairs),
    test_lgg(parent(ann,leo), parent(ann,mira),
             parent(ann,_), shared_subject_kept),
    test_lgg(f(g(a),g(a)),f(g(b),g(b)),
             f(g(Y),g(Y)), nested_pair_sharing),
    test_lgg(f(a),g(a), _, different_functors_are_fresh),
    test_lgg(observation(telescope1,clear),
             observation(telescope2,clear),
             observation(_,clear), astronomy_rule_pattern),
    test_lgg(f(a),f(a),f(a), identical_terms_unchanged),
    test_lgg(f(a),f(a,b),_, arity_mismatch_collapses),
    term_subsumer(pair(a,a),pair(b,b),GShared),
    GShared = pair(S1,S2),
    must((S1==S2), sharing_required),
    term_subsumer(pair(a,a),pair(b,c),GDistinct),
    GDistinct = pair(D1,D2),
    must((D1\==D2), distinct_pairs_must_not_collapse),
    findall(T,term_corpus(T),Terms),
    findall(1,(member(A,Terms),member(B,Terms),
               term_subsumer(A,B,G),
               subsumes_term(G,A),subsumes_term(G,B)),Checks),
    length(Checks, Count),
    must((Count=324), complete_18_by_18_corpus),
    format("D10 SYMBOLIC AI SWI term_subsumer PASS cases=~d; repeated-pair, distinct-pair, structure and arity witnesses~n",[Count]).
