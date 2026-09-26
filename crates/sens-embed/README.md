# my-lisp-embed

`my-lisp-embed` is the narrow C ABI boundary for hosts that need a real,
stateful `my-lisp` session.  It delegates parsing, bootstrap, evaluation,
printing, errors, definitions, macros, and closures to the canonical
`my-lisp` crate; it contains no evaluator or alternate language semantics.

The ABI is intentionally small:

```c
uint32_t my_lisp_embed_abi_version(void);
MyLispEmbedSession *my_lisp_embed_session_new(void);
char *my_lisp_embed_eval(MyLispEmbedSession *, const char *utf8_source);
void my_lisp_embed_free_string(char *);
void my_lisp_embed_session_free(MyLispEmbedSession *);
```

The current ABI version is `4`.  A native host must verify it before using
the other exports.

`my_lisp_embed_eval` evaluates a complete UTF-8 source fragment against the
same session on every call.  The caller owns a non-null returned string and
releases it with `my_lisp_embed_free_string`.  A null session produces a
null pointer.  Parse and language failures are returned as human-readable
`error:` lines, rather than crossing the ABI as panics.

This crate deliberately does **not** define Cyberpunk capabilities.  A host
capability bridge belongs in a later, explicit contract so the RED4ext adapter
remains mechanism while my-lisp retains semantic authority.

## Nullary mechanism bridge

ABI v2 adds one deliberately narrow bridge for a host fact or action with no
arguments.  The host binds a UTF-8 surface to a C callback and may return only
canonical `()` or `t`:

```c
int32_t my_lisp_embed_register_nullary(
    MyLispEmbedSession *session,
    const char *utf8_surface,
    MyLispEmbedNullaryFn callback,
    void *context);
```

The callback is invoked only because Lisp evaluated the bound function.  It
cannot parse source, select a scenario, or run an evaluator.  This covers the
first Cyberpunk mechanisms `запиши-лог` and `гравець-присутній?`; typed
arguments and opaque handles require a later contract.

ABI v3 adds `my_lisp_embed_bind_host_handle`: the host may bind an opaque
value such as `гравець` without exposing its numeric token to Lisp source or
REPL output.

## Typed unary mechanism bridge (#181)

ABI v4 adds a second, still deliberately narrow bridge: a host fact or
action that takes exactly one opaque handle argument of a fixed `kind`
(e.g. `player`):

```c
int32_t my_lisp_embed_register_unary(
    MyLispEmbedSession *session,
    const char *utf8_surface,
    const char *utf8_kind,
    MyLispEmbedUnaryFn callback,
    void *context);
```

The bound Lisp function accepts exactly one argument, which must already be
an opaque handle produced by `my_lisp_embed_bind_host_handle` with a `kind`
that matches `utf8_kind` exactly. Anything else — a handle of a different
`kind`, a non-handle value, or the wrong argument count — becomes an
ordinary Lisp-catchable `error:` result; it never aborts the host process or
falls through to a second, host-defined dispatch layer. The callback itself
receives the handle's `u64` token directly (not a fresh tagged-value
argument protocol), since the only argument shape this mechanism admits is
already fixed by `kind` at registration time.

Like the nullary bridge, the result stays restricted to canonical `()` or
`t` via `out_result` for this first typed-unary increment. A mechanism that
needs to hand back a fresh opaque handle (rather than a boolean fact) is a
later, explicit ABI increment, not something to improvise ad hoc against
this one.
