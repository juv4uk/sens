:- use_module(library(apply)).
:- use_module(library(lists)).

% Independent SWI-Prolog reference for Mackworth (1977), directed arc support.
% A reverse arc is never silently synthesized.
supported(X,Domains,Arcs,V) :-
    \+ (member(arc(X,Y,Relation),Arcs),
        \+ (memberchk(domain(Y,Values),Domains),
            member(W,Values), memberchk(pair(V,W),Relation))).

revise(Domains,Arcs,domain(X,Values),domain(X,Next)) :-
    include(supported(X,Domains,Arcs),Values,Next).

one_round(Domains,Arcs,Next) :-
    maplist(revise(Domains,Arcs),Domains,Next).

fixed_domains(Domains,Arcs,Fixed) :-
    one_round(Domains,Arcs,Next),
    ( Next == Domains -> Fixed = Next
    ; fixed_domains(Next,Arcs,Fixed)).

expect(Actual,Expected,Label) :-
    ( Actual == Expected -> true
    ; format(user_error,'SWI FAIL ~w: actual=~q expected=~q~n',[Label,Actual,Expected]), fail).

mask_values(M,Values) :-
    findall(V,(member(V,[0,1]), Bit is 1<<V, M /\ Bit =\= 0),Values).
mask_pairs(M,Allowed) :-
    findall(pair(X,Y),(member(X,[0,1]),member(Y,[0,1]),
      Bit is 1<<(X*2+Y), M /\ Bit =\= 0),Allowed).

exhaustive_two_var :-
    forall((between(0,3,MA),between(0,3,MB),
            between(0,15,MR),between(0,15,MS)),
      (mask_values(MA,DA),mask_values(MB,DB),mask_pairs(MR,R),mask_pairs(MS,S),
       Domains=[domain(a,DA),domain(b,DB)],
       fixed_domains(Domains,[arc(a,b,R),arc(b,a,S)],Output),
       one_round(Output,[arc(a,b,R),arc(b,a,S)],Again),
       expect(Output,Again,fixpoint_4096),
       forall(member(domain(_,Vals),Output),is_list(Vals)))).

main :-
  fixed_domains([domain(a,[0,1]),domain(b,[0,1])],
      [arc(a,b,[pair(0,1)])],A),
  expect(A,[domain(a,[0]),domain(b,[0,1])],directed_forward),
  fixed_domains([domain(a,[0,1]),domain(b,[0,1])],
      [arc(b,a,[pair(0,1)])],B),
  expect(B,[domain(a,[0,1]),domain(b,[0])],directed_reverse),
  fixed_domains([domain(a,[0,1]),domain(b,[0,1]),domain(c,[1])],
      [arc(a,b,[pair(0,0),pair(1,1)]),
       arc(b,c,[pair(0,0),pair(1,1)])],C),
  expect(C,[domain(a,[1]),domain(b,[1]),domain(c,[1])],revised_chain),
  NE=[pair(0,1),pair(1,0)],
  fixed_domains([domain(a,[0,1]),domain(b,[0,1]),domain(c,[0,1])],
    [arc(a,b,NE),arc(b,a,NE),arc(b,c,NE),arc(c,b,NE),arc(c,a,NE),arc(a,c,NE)],O),
  expect(O,[domain(a,[0,1]),domain(b,[0,1]),domain(c,[0,1])],odd_cycle_locally_consistent),
  \+ (member(X,[0,1]), member(Y,[0,1]),member(Z,[0,1]), X=\=Y,Y=\=Z,Z=\=X),
  fixed_domains([domain(a,[0]),domain(b,[1])],
    [arc(a,b,[pair(0,0)])],Contradiction),
  expect(Contradiction,[domain(a,[]),domain(b,[1])],empty_domain_contradiction),
  exhaustive_two_var,
  writeln('D10-4991-SWI PASS native Prolog 4096 two-variable CSPs, directed asymmetry, chain, odd-cycle; 0 coordinates'),
  halt(0).

:- initialization(main,main).
