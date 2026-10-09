% External SWI-Prolog finite-state GPS means/ends reference model.
% (role research-only)
% (semantic-authority-change none)
% This is a modern constrained reconstruction of GPS 1958 difference-operator
% connections, NOT original IPL-V runtime and NOT executable binary SENS.
:- use_module(library(ordsets)).
:- initialization(main, main).

wellformed(U,S,G,op(P,A,D)) :-
    is_ordset(U),
    maplist(is_ordset,[S,G,P,A,D]),
    ord_subset(S,U), ord_subset(G,U),
    ord_subset(P,U), ord_subset(A,U), ord_subset(D,U),
    ord_disjoint(A,D).

% The explicit "relevant" witness never claims progress or completion.
gps_link(U,S,G,Op,link(Missing,Unwanted,AddHit,DelHit,Needed,Ready,Next,Relevant)) :-
    wellformed(U,S,G,Op),
    Op=op(P,A,D),
    ord_subtract(G,S,Missing),
    ord_subtract(S,G,Unwanted),
    ord_intersection(A,Missing,AddHit),
    ord_intersection(D,Unwanted,DelHit),
    ord_subtract(P,S,Needed),
    (Needed=[] ->
       Ready=true, ord_subtract(S,D,Without),ord_union(Without,A,Next)
    ;  Ready=false,Next=blocked),
    ord_union(AddHit,DelHit,Hits),
    (Hits=[] -> Relevant=false ; Relevant=true).

check(Label,Goal) :-
    (call(Goal) ->
       format('GPS-OBS\t~w\tPASS~n',[Label]),
       nb_getval(count,C0),C1 is C0+1,nb_setval(count,C1)
    ; format(user_error,'GPS FAIL: ~w~n',[Label]),halt(1)).

main :-
    nb_setval(count,0),
    check(missing_atom,
      gps_link([battery,signal],[battery],[battery,signal],
        op([battery],[signal],[]),
        link([signal],[],[signal],[],[],true,[battery,signal],true))),
    check(missing_precondition_creates_subgoal,
      gps_link([battery,power,signal],[power],[power,signal],
        op([battery],[signal],[]),
        link([signal],[],[signal],[],[battery],false,blocked,true))),
    check(unwanted_true_atom_is_difference,
      gps_link([noise,signal],[noise,signal],[signal],
        op([],[],[noise]),
        link([],[noise],[],[noise],[],true,[signal],true))),
    check(unwanted_removal_blocked,
      gps_link([lock,noise,signal],[noise,signal],[signal],
        op([lock],[],[noise]),
        link([],[noise],[],[noise],[lock],false,blocked,true))),
    check(irrelevant_side_effect,
      gps_link([battery,noise,signal],[battery],[battery,signal],
        op([],[noise],[]),
        link([signal],[],[],[],[],true,[battery,noise],false))),
    check(complete_goal_has_no_relevant_effect,
      gps_link([battery,noise],[battery],[battery],
        op([],[noise],[]),
        link([],[],[],[],[],true,[battery,noise],false))),
    check(relevant_not_progress_certificate,
      gps_link([battery,signal],[battery],[battery,signal],
        op([],[signal],[battery]),
        link([signal],[],[signal],[],[],true,[signal],true))),
    check(add_satisfied_goal_not_witness,
      gps_link([battery,signal],[battery],[battery,signal],
        op([],[battery],[]),
        link([signal],[],[],[],[],true,[battery],false))),
    check(precondition_unrelated_to_relevance,
      gps_link([battery,noise,signal],[battery],[battery,signal],
        op([signal],[noise],[]),
        link([signal],[],[],[],[signal],false,blocked,false))),
    check(irrelevant_operator_can_be_applicable,
      gps_link([battery,signal],[battery],[battery,signal],
        op([],[battery],[]),
        link([signal],[],[],[],[],true,[battery],false))),
    check(empty_universe,
      gps_link([],[],[],op([],[],[]),
        link([],[],[],[],[],true,[],false))),
    check(negative_invalid_state,
      \+ gps_link([a],[z],[],op([],[],[]),_)),
    check(negative_invalid_goal,
      \+ gps_link([a],[],[z],op([],[],[]),_)),
    check(negative_invalid_precondition,
      \+ gps_link([a],[],[a],op([z],[a],[]),_)),
    check(negative_conflicting_add_delete_effect,
      \+ gps_link([a],[],[a],op([],[a],[a]),_)),
    check(negative_duplicate_atoms_forbidden,
      \+ gps_link([a],[a,a],[a],op([],[],[]),_)),
    check(negative_unsorted_atoms_forbidden,
      \+ gps_link([a,b],[b,a],[a],op([],[],[]),_)),
    nb_getval(count,N),
    format('GPS-SUMMARY\tRECONSTRUCTION-NOT-ORIGINAL-IPL\t~d~n',[N]),
    current_prolog_flag(version_data,swi(Maj,Min,Patch,_)),
    format('GPS-DONOR\tSWI-PROLOG\t~d.~d.~d~n',[Maj,Min,Patch]),
    halt(0).
