:- use_module(library(assoc)).
:- use_module(library(lists)).

% Independent SWI-Prolog oracle. It compares the AST rewrite against a
% separate exact polynomial-coefficient algebra, not against Python output.

run :-
    findall(E, (between(0, 2, H), expr_at_height(H, E)), Raw),
    sort(Raw, Expressions),
    forall((member(E, Expressions), member(Target, [x, y])),
           check_derivative(E, Target)),
    length(Expressions, ExpressionCount),
    ComparisonCount is ExpressionCount * 2,
    format('D10-MALING-PROLOG-ORACLE PASS expressions=~d comparisons=~d~n',
           [ExpressionCount, ComparisonCount]).

expr_at_height(0, c(-1)).
expr_at_height(0, c(0)).
expr_at_height(0, c(2)).
expr_at_height(0, v(x)).
expr_at_height(0, v(y)).
expr_at_height(H, Expr) :-
    integer(H), H > 0,
    H0 is H - 1,
    expr_at_leq(H0, Left),
    expr_at_leq(H0, Right),
    tree_height(Left, HL),
    tree_height(Right, HR),
    max_list([HL, HR], H0),
    ( Expr = add(Left, Right)
    ; Expr = mul(Left, Right)
    ).

expr_at_leq(Max, Expr) :-
    between(0, Max, Height),
    expr_at_height(Height, Expr).

tree_height(c(_), 0).
tree_height(v(_), 0).
tree_height(add(A, B), H) :-
    tree_height(A, HA), tree_height(B, HB), H is max(HA, HB) + 1.
tree_height(mul(A, B), H) :-
    tree_height(A, HA), tree_height(B, HB), H is max(HA, HB) + 1.

derive(c(_), _, c(0)).
derive(v(Name), Target, c(1)) :-
    Name == Target, !.
derive(v(_), _, c(0)).
derive(add(A, B), Target, add(DA, DB)) :-
    derive(A, Target, DA),
    derive(B, Target, DB).
derive(mul(A, B), Target, add(mul(DA, B), mul(A, DB))) :-
    derive(A, Target, DA),
    derive(B, Target, DB).

check_derivative(Expr, Target) :-
    derive(Expr, Target, ActualExpr),
    polynomial(Expr, SourcePoly),
    polynomial(ActualExpr, ActualPoly),
    derivative_polynomial(Target, SourcePoly, ExpectedPoly),
    assoc_to_list(ActualPoly, Actual),
    assoc_to_list(ExpectedPoly, Expected),
    ( Actual == Expected ->
        true
    ;
        throw(error(maling_derivative_mismatch(Expr, Target, Actual, Expected), _))
    ).

% A polynomial is an assoc from a canonical monomial to an exact integer.
% A monomial is a sorted list of Variable-Exponent pairs.
polynomial(c(N), Poly) :-
    empty_assoc(Empty),
    add_term([], N, Empty, Poly).
polynomial(v(Name), Poly) :-
    empty_assoc(Empty),
    add_term([Name-1], 1, Empty, Poly).
polynomial(add(A, B), Poly) :-
    polynomial(A, PA),
    polynomial(B, PB),
    assoc_to_list(PB, Terms),
    add_terms(Terms, PA, Poly).
polynomial(mul(A, B), Poly) :-
    polynomial(A, PA),
    polynomial(B, PB),
    assoc_to_list(PA, LA),
    assoc_to_list(PB, LB),
    empty_assoc(Empty),
    multiply_terms(LA, LB, Empty, Poly).

add_term(_, 0, Poly, Poly) :- !.
add_term(Monomial, Coefficient, Before, After) :-
    ( get_assoc(Monomial, Before, Old) ->
        New is Old + Coefficient
    ;
        New = Coefficient
    ),
    ( New =:= 0 ->
        ( del_assoc(Monomial, Before, _, After) -> true ; After = Before )
    ;
        put_assoc(Monomial, Before, New, After)
    ).

add_terms([], Poly, Poly).
add_terms([Monomial-Coefficient|Rest], Before, After) :-
    add_term(Monomial, Coefficient, Before, Next),
    add_terms(Rest, Next, After).

multiply_terms([], _, Poly, Poly).
multiply_terms([MA-CA|Rest], Right, Before, After) :-
    multiply_row(MA, CA, Right, Before, Next),
    multiply_terms(Rest, Right, Next, After).

multiply_row(_, _, [], Poly, Poly).
multiply_row(MA, CA, [MB-CB|Rest], Before, After) :-
    merge_monomials(MA, MB, ProductMonomial),
    ProductCoefficient is CA * CB,
    add_term(ProductMonomial, ProductCoefficient, Before, Next),
    multiply_row(MA, CA, Rest, Next, After).

merge_monomials([], B, B).
merge_monomials(A, [], A).
merge_monomials([V-EA|As], [W-EB|Bs], [V-E|Rest]) :-
    V == W, !,
    E is EA + EB,
    merge_monomials(As, Bs, Rest).
merge_monomials([V-EA|As], [W-EB|Bs], [V-EA|Rest]) :-
    V @< W, !,
    merge_monomials(As, [W-EB|Bs], Rest).
merge_monomials([V-EA|As], [W-EB|Bs], [W-EB|Rest]) :-
    merge_monomials([V-EA|As], Bs, Rest).

derivative_polynomial(Target, Polynomial, Derivative) :-
    assoc_to_list(Polynomial, Terms),
    empty_assoc(Empty),
    derive_polynomial_terms(Terms, Target, Empty, Derivative).

derive_polynomial_terms([], _, Poly, Poly).
derive_polynomial_terms([Monomial-Coefficient|Rest], Target, Before, After) :-
    decrement_power(Monomial, Target, ReducedMonomial, Exponent),
    ( Exponent > 0 ->
        NewCoefficient is Coefficient * Exponent,
        add_term(ReducedMonomial, NewCoefficient, Before, Next)
    ;
        Next = Before
    ),
    derive_polynomial_terms(Rest, Target, Next, After).

decrement_power([], _, [], 0).
decrement_power([Name-Exponent|Rest], Target, Reduced, FoundExponent) :-
    Name == Target, !,
    FoundExponent = Exponent,
    ( Exponent =:= 1 ->
        Reduced = Rest
    ;
        NewExponent is Exponent - 1,
        Reduced = [Name-NewExponent|Rest]
    ).
decrement_power([Pair|Rest], Target, [Pair|Reduced], Exponent) :-
    decrement_power(Rest, Target, Reduced, Exponent).

