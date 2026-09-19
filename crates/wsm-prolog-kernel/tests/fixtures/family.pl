parent(alice, bob).
parent(bob, carol).
parent(alice, dave).

ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).

% Same answer through two independent proof paths.
duplicate_path(alice).
duplicate_path(alice).
