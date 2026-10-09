use sens::{lower_program, parse, parse_canonical_binary, Expr, ExprKind};

fn trace(expr: &Expr) -> String {
    match &expr.kind {
        ExprKind::DomainIdentity(id) => format!("id:D{}:{:0width$b}", id.width(), id.packed_bits(), width=id.width()),
        ExprKind::DomainCall(id, args) => {
            let mut out = format!("call:D{}:{:0width$b}[", id.width(), id.packed_bits(), width=id.width());
            for (i, arg) in args.iter().enumerate() {
                if i > 0 { out.push(','); }
                out.push_str(&trace(arg));
            }
            out.push(']');
            out
        }
        ExprKind::List(items) => {
            let mut out = "list[".to_owned();
            for (i, item) in items.iter().enumerate() {
                if i > 0 { out.push(','); }
                out.push_str(&trace(item));
            }
            out.push(']');
            out
        }
        ExprKind::Pair(head, tail) => format!("pair[{},{}]", trace(head), trace(tail)),
        ExprKind::Sid(_) | ExprKind::Call(_, _) => {
            panic!("legacy byte identity entered current D1-D8 preflight")
        }
        other => panic!("unsupported node in Number/local-free preflight: {other:?}"),
    }
}

fn lowered_english(source: &str) -> Vec<String> {
    lower_program(&parse(source).expect("English surface parses"))
        .iter()
        .map(trace)
        .collect()
}

fn lowered_binary(source: &str) -> Vec<String> {
    lower_program(&parse_canonical_binary(source).expect("canonical binary parses"))
        .iter()
        .map(trace)
        .collect()
}

#[test]
fn current_english_and_canonical_binary_match_on_d3_number_local_free_subset() {
    let cases = [
        (
            "(quote ())",
            "10 001 00 10 01 01",
        ),
        (
            "(car (quote ()))",
            "10 101 00 10 001 00 10 01 01 01",
        ),
        (
            "(cdr (quote ()))",
            "10 110 00 10 001 00 10 01 01 01",
        ),
        (
            "(cons (quote ()) (quote ()))",
            "10 100 00 10 001 00 10 01 01 00 10 001 00 10 01 01 01",
        ),
        (
            "(eq? (quote ()) (quote ()))",
            "10 111 00 10 001 00 10 01 01 00 10 001 00 10 01 01 01",
        ),
        (
            "(atom? (quote ()))",
            "10 010 00 10 001 00 10 01 01 01",
        ),
    ];

    for (english, binary) in cases {
        assert_eq!(
            lowered_english(english),
            lowered_binary(binary),
            "semantic trace mismatch\nEnglish: {english}\nBinary: {binary}"
        );
    }
}
