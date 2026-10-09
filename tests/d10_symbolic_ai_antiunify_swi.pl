% Independent real SWI-Prolog donor for D10 research-only ground-term LGG.
% Not an implementation of SENS binary semantics.
:- use_module(library(terms)).

test_lgg :-
    term_subsumer(f(a,a), f(b,b), G1),
    G1 =@= f(X,X),
    subsumes_term(G1, f(a,a)),
    subsumes_term(G1, f(b,b)),

    term_subsumer(f(a,b), f(b,a), G2),
    G2 =@= f(A,B),
    A \== B,
    subsumes_term(G2, f(a,b)),
    subsumes_term(G2, f(b,a)),

    term_subsumer(f(a,g(a)), f(b,g(b)), G3),
    G3 =@= f(Y,g(Y)),

    term_subsumer(f(a), g(a), Mismatch),
    var(Mismatch),

    term_subsumer(f(a), f(a), Same),
    Same == f(a),

    \+ subsumes_term(f(Z,Z), f(a,b)).

main :-
    ( test_lgg ->
        writeln('SWI-FIRST-ORDER-LGG: PASS'),
        halt(0)
    ;   writeln(user_error, 'SWI-FIRST-ORDER-LGG: FAIL'),
        halt(1)
    ).

:- initialization(main, main).
