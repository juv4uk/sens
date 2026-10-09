:- use_module(library(http/json)).
:- use_module(library(clpfd)).

% Independent whole-network round consistency oracle. No Python imports.
% A directed arc only prunes its SOURCE, never an implicit reverse arc.
normalize(Input, Pairs, Arcs) :-
    get_dict(domains, Input, Ds),
    dict_pairs(Ds, _, Original),
    maplist(sorted_domain, Original, Pairs),
    get_dict(arcs, Input, Raw),
    maplist(arc_term, Raw, Arcs).

sorted_domain(Key-Vals, Key-Sorted) :- sort(Vals, Sorted).

arc_term(Dict, arc(A,B,Pairs)) :-
    get_dict(from, Dict, From), get_dict(to, Dict, To),
    atom_string(A, From), atom_string(B, To),
    get_dict(allowed, Dict, Pairs).

% Check a table using the built-in SWI CLP(FD) relation as an
% independent source oracle. Query one arc only: global SAT propagation
% must never be substituted for ARC consistency.
pair_supported(V, OtherDomain, Pairs) :-
    member(W, OtherDomain),
    X #= V, Y #= W,
    tuples_in([[X,Y]], Pairs),
    !.

all_arc_supports(_, _, [], _).
all_arc_supports(Name, V, [arc(From,To,Pairs)|Rest], Domains) :-
    ( Name == From ->
        memberchk(To-OtherDomain, Domains),
        pair_supported(V, OtherDomain, Pairs)
    ; true
    ),
    all_arc_supports(Name, V, Rest, Domains).

retain(Domains, Arcs, Name-Values, Name-Retained) :-
    include({Name,Domains,Arcs}/[V]>>all_arc_supports(Name,V,Arcs,Domains),
            Values, Retained).

round_state(Domains, Arcs, Next) :-
    maplist(retain(Domains,Arcs), Domains, Next).

fixed_state(Domains, Arcs, Final) :-
    round_state(Domains, Arcs, Next),
    ( Domains == Next -> Final = Domains
    ; fixed_state(Next, Arcs, Final)
    ).

status(Domains, "EMPTY-DOMAIN-CONTRADICTION") :-
    member(_-[], Domains), !.
status(_, "ARC-CONSISTENT").

solve(Input, Out) :-
    normalize(Input, Domains, Arcs),
    fixed_state(Domains, Arcs, Final),
    dict_pairs(Dict, json, Final),
    status(Final, Status),
    Out = _{domains:Dict, status:Status}.

loop :-
    read_line_to_string(user_input, Line),
    ( Line == end_of_file -> true
    ; Line == "" -> loop
    ; atom_string(SourceAtom, Line),
      atom_json_dict(SourceAtom, Input, []),
      solve(Input, Out),
      json_write_dict(current_output, Out), nl,
      flush_output,
      loop
    ).

:- initialization(loop, main).
