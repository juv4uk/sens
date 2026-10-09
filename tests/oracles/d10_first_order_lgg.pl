% Independent executable SWI-Prolog witness for D10 first-order LGG HOLD.
% It is NOT a native SENS implementation. Input: a JSON array from a file.
% Atom: {"a":"..."} ; constructor: {"f":"...", "args":[...]}.
% json_read_dict/2 yields anonymous dict tags that are variables; `==` would
% mistake two equal JSON terms for different objects. `=@=` compares variants.
% Output: JSON array generalizer + TWO explicit ground reconstructions.
:- use_module(library(http/json)).
:- initialization(main, main).

lookup_pair([pair(X, Y, Hole) | _], A, B, Hole) :-
    X =@= A, Y =@= B, !.
lookup_pair([_ | Rest], A, B, Hole) :-
    lookup_pair(Rest, A, B, Hole).

join_args([], [], S, S, []).
join_args([A | As], [B | Bs], S0, S2, [G | Gs]) :-
    anti(A, B, S0, S1, G),
    join_args(As, Bs, S1, S2, Gs).

anti(A, B, S0, S1, G) :-
    ( A =@= B ->
        G = A, S1 = S0
    ; is_dict(A), is_dict(B),
      get_dict(f, A, FA), get_dict(f, B, FB), FA == FB,
      get_dict(args, A, As), get_dict(args, B, Bs),
      same_length(As, Bs) ->
        join_args(As, Bs, S0, S1, Gs),
        G = _{f:FA, args:Gs}
    ; S0 = state(Pairs, N, L, R),
      ( lookup_pair(Pairs, A, B, Existing) ->
          G = _{hole:Existing}, S1 = S0
      ; format(string(New), "V~d", [N]),
        N1 is N + 1,
        G = _{hole:New},
        S1 = state([pair(A, B, New) | Pairs], N1,
                   [_{hole:New, term:A} | L], [_{hole:New, term:B} | R])
      )
    ).

run_case(Case, Out) :-
    get_dict(left, Case, A), get_dict(right, Case, B),
    anti(A, B, state([], 0, [], []), state(_, _, ReversedL, ReversedR), G),
    reverse(ReversedL, LeftSub), reverse(ReversedR, RightSub),
    Out = _{generalizer:G, left_substitution:LeftSub,
            right_substitution:RightSub}.

main :-
    current_prolog_flag(argv, [Source]),
    setup_call_cleanup(open(Source, read, Stream, [encoding(utf8)]),
                       json_read_dict(Stream, Cases),
                       close(Stream)),
    is_list(Cases),
    maplist(run_case, Cases, Results),
    json_write(current_output, Results, [width(0)]),
    nl,
    halt(0).
main :-
    writeln(user_error, 'BLOCKED: Prolog oracle expected JSON list and one input file'),
    halt(2).
