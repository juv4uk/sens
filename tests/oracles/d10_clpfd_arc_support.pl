% Real CLP(FD) witness. SWI-Prolog tuples_in/2 is the INDEPENDENT donor.
% This is not SENS execution; no D10 bit identity is allocated.
:- use_module(library(clpfd)).
:- use_module(library(http/json)).
:- use_module(library(lists)).
:- initialization(main, main).

no_support(_{status:"NO-SUPPORT",left:[],right:[]}).

solve_case(Case, Result) :-
    Left = Case.left,
    Right = Case.right,
    Relation = Case.relation,
    (   Left == []
    ->  no_support(Result)
    ;   Right == []
    ->  no_support(Result)
    ;   Relation == []
    ->  no_support(Result)
    ;   list_to_fdset(Left, LeftSet),
        list_to_fdset(Right, RightSet),
        (   X in_set LeftSet,
            Y in_set RightSet,
            tuples_in([[X,Y]], Relation),
            findall([X,Y], labeling([], [X,Y]), Pairs),
            Pairs \== []
        ->  findall(A, member([A,_], Pairs), As),
            findall(B, member([_,B], Pairs), Bs),
            sort(As, XS),
            sort(Bs, YS),
            Result = _{status:"SUPPORTED",left:XS,right:YS}
        ;   no_support(Result)
        )
    ).

main([InputPath, OutputPath]) :-
    setup_call_cleanup(
        open(InputPath, read, Input, [encoding(utf8)]),
        json_read_dict(Input, Cases),
        close(Input)),
    maplist(solve_case, Cases, Results),
    setup_call_cleanup(
        open(OutputPath, write, Output, [encoding(utf8)]),
        json_write_dict(Output, Results, [width(0)]),
        close(Output)),
    length(Results, N),
    format('D10-SYMBOLIC-CLP: SWI-Prolog real tuples_in/2 executed ~d cases~n', [N]).
main(Args) :-
    format(user_error, 'D10-SYMBOLIC-CLP: expected input.json output.json, got ~w~n', [Args]),
    halt(2).
