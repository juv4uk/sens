use sens::{
    load_core_library, load_tcp_library, parse_mixed_exact_domain_process_tcp_source, ExprKind,
    Session,
};

#[test]
fn tcp_d9_head_uses_the_ratified_identity_and_loads_from_t5m() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_tcp_library(&mut session).expect("TCP text layer through Zig/T5M");

    let parsed = parse_mixed_exact_domain_process_tcp_source(
        "lib/tcp.lisp",
        "(протокол-передавання-читати-байти-текст (список 104 105))",
    )
    .expect("the pinned Ukrainian head resolves through the D9 ladder");
    let ExprKind::List(items) = &parsed[0].kind else {
        panic!("TCP function application");
    };
    assert!(
        matches!(&items[0].kind, ExprKind::DomainIdentity(identity)
            if identity.width() == 9 && identity.packed_bits() == 0b001101001),
        "the call head is the exact D9 resident, not a D7 or inferred-width alias"
    );

    for capability in [
        "process-run-raw",
        "tcp-read-raw",
        "read-file-bytes",
        "записати-байти-файла",
    ] {
        assert!(
            session.environment.get(capability).is_none(),
            "loading the TCP language layer must not grant host capability {capability}"
        );
    }
}
