#!/usr/bin/env python3
# Механічна міграція Value::Pair(Rc<Value>, Rc<Value>) -> Value::Pair(Rc<PairNode>) (#5950, крок 2).
# Запуск: python3 scripts/migrate-pair-to-pairnode.py [шлях-до-кореня-репо]
# Скрипт виходить з помилкою, якщо хоч одна правка не збіглася (захист від дрейфу репо).
# Mechanical migration of Value::Pair(Rc<Value>, Rc<Value>) -> Value::Pair(Rc<PairNode>).
import sys

import os
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
if not ROOT.endswith("/"): ROOT += "/"

# file -> list of (old, new, count) ; count None means replace_all
OPS = {}

def add(path, old, new, count=1):
    OPS.setdefault(path, []).append((old, new, count))

# ---------- crates/sens/src/compiler_bootstrap.rs ----------
f = "crates/sens/src/compiler_bootstrap.rs"
add(f, "use crate::{sha256_source, ErrorKind, Exactness, LanguageError, Value};",
       "use crate::{sha256_source, ErrorKind, Exactness, LanguageError, PairNode, Value};")
add(f, """        Value::Pair(head, tail) => {
            out.push(0x04);
            encode_canonical_compiler_value(head, out)?;
            encode_canonical_compiler_value(tail, out)?;
        }""",
       """        Value::Pair(node) => {
            out.push(0x04);
            encode_canonical_compiler_value(&node.head, out)?;
            encode_canonical_compiler_value(&node.tail, out)?;
        }""")
add(f, "                Ok(Value::Pair(Rc::new(head), Rc::new(tail)))",
       "                Ok(Value::Pair(Rc::new(PairNode { head, tail })))")
add(f, """            let Value::Pair(head, tail) = &cursor else {
                panic!("round-trip list must retain all exact-width identities");
            };
            let Value::DomainIdentity(identity) = head.as_ref() else {
                panic!("round-trip item must remain an exact DomainIdentity");
            };
            assert_eq!(identity.width(), expected_width);
            assert_eq!(identity.packed_bits(), 1);
            cursor = tail.as_ref().clone();""",
       """            let Value::Pair(node) = &cursor else {
                panic!("round-trip list must retain all exact-width identities");
            };
            let Value::DomainIdentity(identity) = &node.head else {
                panic!("round-trip item must remain an exact DomainIdentity");
            };
            assert_eq!(identity.width(), expected_width);
            assert_eq!(identity.packed_bits(), 1);
            cursor = node.tail.clone();""")

# ---------- crates/sens/src/compiler_language.rs ----------
f = "crates/sens/src/compiler_language.rs"
add(f, """            Value::Pair(head, tail) => {
                items.push(head.as_ref());
                cursor = tail.as_ref();""",
       """            Value::Pair(node) => {
                items.push(&node.head);
                cursor = &node.tail;""")
add(f, """                Value::Pair(head, tail) => {
                    out.push(head.as_ref());
                    cursor = tail.as_ref();""",
       """                Value::Pair(node) => {
                    out.push(&node.head);
                    cursor = &node.tail;""")

# ---------- crates/sens/src/eval/canon.rs ----------
f = "crates/sens/src/eval/canon.rs"
add(f, """                        Value::Pair(head, tail) => {
                            items.push(head.as_ref().clone());
                            cursor = tail.as_ref();""",
       """                        Value::Pair(node) => {
                            items.push(node.head.clone());
                            cursor = &node.tail;""")

# ---------- crates/sens/src/eval/closures.rs ----------
f = "crates/sens/src/eval/closures.rs"
add(f, '                    Value::Pair(_, _) => "пара",', '                    Value::Pair(_) => "пара",')
add(f, "        Value::Pair(_, _) => {\n            let mut items = Vec::new();", "        Value::Pair(_) => {\n            let mut items = Vec::new();")
add(f, """                    Value::Pair(h, t) => {
                        items.push(go(h, span, depth + 1)?);
                        current = (**t).clone();
                    }""",
       """                    Value::Pair(node) => {
                        items.push(go(&node.head, span, depth + 1)?);
                        current = node.tail.clone();
                    }""")

# ---------- crates/sens/src/eval/mod.rs ----------
f = "crates/sens/src/eval/mod.rs"
add(f, '                    Value::Pair(_, _) => "пара",', '                    Value::Pair(_) => "пара",')
add(f, "assert!(matches!(result.value, Value::Pair(_, _)));", "assert!(matches!(result.value, Value::Pair(_)));")

# ---------- crates/sens/src/eval/selector_law.rs ----------
f = "crates/sens/src/eval/selector_law.rs"
add(f, """        Value::Pair(
            std::rc::Rc::new(full_pair_tree(depth - 1, first)),
            std::rc::Rc::new(full_pair_tree(depth - 1, first)),
        )""",
       """        Value::Pair(std::rc::Rc::new(crate::PairNode {
            head: full_pair_tree(depth - 1, first),
            tail: full_pair_tree(depth - 1, first),
        }))""")

# ---------- crates/sens/src/eval/special_forms/core.rs ----------
f = "crates/sens/src/eval/special_forms/core.rs"
add(f, """use crate::{
    Bit4, CoreD4, CoreDomainIdentity, Environment, ErrorKind, Expr, ExprKind, LanguageError, Span,
    Value,
};""",
       """use crate::{
    Bit4, CoreD4, CoreDomainIdentity, Environment, ErrorKind, Expr, ExprKind, LanguageError,
    PairNode, Span, Value,
};""")
add(f, "Value::predicate_bit(!matches!(value, Value::Pair(_, _)))",
       "Value::predicate_bit(!matches!(value, Value::Pair(_)))")
add(f, """            ExprKind::Pair(head, tail) => {
                Value::Pair(Rc::new(go(head, depth + 1)?), Rc::new(go(tail, depth + 1)?))
            }""",
       """            ExprKind::Pair(head, tail) => Value::Pair(Rc::new(PairNode {
                head: go(head, depth + 1)?,
                tail: go(tail, depth + 1)?,
            })),""")
add(f, "        Value::Pair(ref head, _) => Ok((**head).clone()),",
       "        Value::Pair(node) => Ok(node.head.clone()),")
add(f, "        Value::Pair(_, ref tail) => Ok((**tail).clone()),",
       "        Value::Pair(node) => Ok(node.tail.clone()),")
add(f, "    Ok(Value::Pair(std::rc::Rc::new(head), std::rc::Rc::new(tail)))",
       "    Ok(Value::Pair(std::rc::Rc::new(PairNode { head, tail })))")

# ---------- crates/sens/src/eval/special_forms/io.rs ----------
f = "crates/sens/src/eval/special_forms/io.rs"
add(f, "        Value::Pair(head, tail) => contains_predicate_bit(head) || contains_predicate_bit(tail),",
       "        Value::Pair(node) => contains_predicate_bit(&node.head) || contains_predicate_bit(&node.tail),")

# ---------- crates/sens/src/eval/special_forms/json.rs ----------
f = "crates/sens/src/eval/special_forms/json.rs"
add(f, "use crate::Value;", "use crate::{PairNode, Value};")
add(f, """            alist = Value::Pair(
                Rc::new(Value::Pair(Rc::new(key), Rc::new(value))),
                Rc::new(alist),
            );""",
       """            alist = Value::Pair(Rc::new(PairNode {
                head: Value::Pair(Rc::new(PairNode { head: key, tail: value })),
                tail: alist,
            }));""")

# ---------- crates/sens/src/presentation.rs ----------
f = "crates/sens/src/presentation.rs"
add(f, "        Value::Pair(_, _) => render_pair_uk(value),", "        Value::Pair(_) => render_pair_uk(value),")
add(f, """            Value::Pair(head, tail) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_uk(head));
                current = tail;
                first = false;
            }""",
       """            Value::Pair(node) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_uk(&node.head));
                current = &node.tail;
                first = false;
            }""")
add(f, "        Value::Pair(_, _) => {\n            let mut output = String::from(\"(\");", "        Value::Pair(_) => {\n            let mut output = String::from(\"(\");")
add(f, """                    Value::Pair(head, tail) => {
                        if !first {
                            output.push(' ');
                        }
                        output.push_str(&render_sa(head));
                        current = tail;
                        first = false;
                    }""",
       """                    Value::Pair(node) => {
                        if !first {
                            output.push(' ');
                        }
                        output.push_str(&render_sa(&node.head));
                        current = &node.tail;
                        first = false;
                    }""")

# ---------- crates/sens/src/program_data.rs ----------
f = "crates/sens/src/program_data.rs"
add(f, "use crate::{DomainIdentity, ErrorKind, Expr, ExprKind, LanguageError, Span, Value};",
       "use crate::{DomainIdentity, ErrorKind, Expr, ExprKind, LanguageError, PairNode, Span, Value};")
add(f, """        ExprKind::Pair(head, tail) => Value::Pair(
            Rc::new(expr_to_exact_program_data(head)?),
            Rc::new(expr_to_exact_program_data(tail)?),
        ),""",
       """        ExprKind::Pair(head, tail) => Value::Pair(Rc::new(PairNode {
            head: expr_to_exact_program_data(head)?,
            tail: expr_to_exact_program_data(tail)?,
        })),""")
add(f, "assert!(matches!(result, Value::Pair(_, _)));", "assert!(matches!(result, Value::Pair(_)));")

# ---------- crates/sens-cli/src/bin/wsm-fs-record-consumer.rs ----------
f = "crates/sens-cli/src/bin/wsm-fs-record-consumer.rs"
add(f, """    let Value::Pair(root_tag, _) = &root else {
        std::process::exit(1)
    };
    let Value::Symbol(tag) = &**root_tag else {""",
       """    let Value::Pair(root_node) = &root else {
        std::process::exit(1)
    };
    let Value::Symbol(tag) = &root_node.head else {""")
add(f, """    let Value::Pair(ref tag, _) = rebuilt else {
        std::process::exit(1)
    };
    if !matches!(&**tag, Value::Symbol(name) if &**name == "accepted") {""",
       """    let Value::Pair(ref node) = rebuilt else {
        std::process::exit(1)
    };
    if !matches!(&node.head, Value::Symbol(name) if &**name == "accepted") {""")

# ---------- crates/sens-cli/src/bin/wsm-fs-record-producer.rs ----------
f = "crates/sens-cli/src/bin/wsm-fs-record-producer.rs"
add(f, """            Value::Pair(head, tail) => {
                let Value::String(record) = &**head else {
                    eprintln!("wsm-fs-record-producer: record is not a string");
                    std::process::exit(1);
                };
                records.push(record.to_string());
                value = (**tail).clone();
            }""",
       """            Value::Pair(node) => {
                let Value::String(record) = &node.head else {
                    eprintln!("wsm-fs-record-producer: record is not a string");
                    std::process::exit(1);
                };
                records.push(record.to_string());
                value = node.tail.clone();
            }""")

# ---------- crates/sens-cli/src/repl.rs ----------
f = "crates/sens-cli/src/repl.rs"
add(f, """use sens::{
    eval_program, render_value_for_presentation, BinaryNumber, CoreDomainIdentity, DomainIdentity,
    Environment, ExactDomainWord, Expr, ExprKind, PhysicalT5Program, PresentationLanguage, Session,
    Value,
};""",
       """use sens::{
    eval_program, render_value_for_presentation, BinaryNumber, CoreDomainIdentity, DomainIdentity,
    Environment, ExactDomainWord, Expr, ExprKind, PairNode, PhysicalT5Program, PresentationLanguage,
    Session, Value,
};""")
add(f, """        Value::Pair(head, tail) => ExprKind::Pair(
            std::rc::Rc::new(exact_t5m_result_data(head, depth + 1)?),
            std::rc::Rc::new(exact_t5m_result_data(tail, depth + 1)?),
        ),""",
       """        Value::Pair(node) => ExprKind::Pair(
            std::rc::Rc::new(exact_t5m_result_data(&node.head, depth + 1)?),
            std::rc::Rc::new(exact_t5m_result_data(&node.tail, depth + 1)?),
        ),""")
add(f, "        Value::Pair(_, _) => render_repl_pair(value, language),", "        Value::Pair(_) => render_repl_pair(value, language),")
add(f, """            Value::Pair(head, tail) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_repl_reply(head, language));
                current = tail;
                first = false;
            }""",
       """            Value::Pair(node) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_repl_reply(&node.head, language));
                current = &node.tail;
                first = false;
            }""")
add(f, """        let Value::Pair(head, _) = &value else {
            panic!("list");
        };
        assert_eq!(head.as_ref(), &Value::Symbol("car".into()));""",
       """        let Value::Pair(node) = &value else {
            panic!("list");
        };
        assert_eq!(&node.head, &Value::Symbol("car".into()));""")
add(f, """        let dotted = Value::Pair(
            std::rc::Rc::new(Value::Symbol("left".into())),
            std::rc::Rc::new(Value::Symbol("right".into())),
        );""",
       """        let dotted = Value::Pair(std::rc::Rc::new(PairNode {
            head: Value::Symbol("left".into()),
            tail: Value::Symbol("right".into()),
        }));""")

# ---------- crates/sens-cli/src/swarm.rs ----------
f = "crates/sens-cli/src/swarm.rs"
add(f, """    while let Value::Pair(head, tail) = value {
        items.push((**head).clone());
        value = tail;
    }""",
       """    while let Value::Pair(node) = value {
        items.push(node.head.clone());
        value = &node.tail;
    }""")
add(f, """        Value::Pair(k, v) => match &**k {
            Value::Symbol(name) if &**name == key => Some((**v).clone()),
            _ => None,
        },""",
       """        Value::Pair(node) => match &node.head {
            Value::Symbol(name) if &**name == key => Some(node.tail.clone()),
            _ => None,
        },""")
add(f, "            matches!(value, Value::Pair(_, _) | Value::Nil),", "            matches!(value, Value::Pair(_) | Value::Nil),")

# ---------- crates/sens-host/src/lib.rs ----------
f = "crates/sens-host/src/lib.rs"
add(f, """            Value::Pair(head, tail) => {
                // SENS arithmetic now returns exactly qualified D24+ numbers.""",
       """            Value::Pair(node) => {
                // SENS arithmetic now returns exactly qualified D24+ numbers.""")
add(f, "                let byte = match &**head {", "                let byte = match &node.head {")
add(f, """                bytes.push(byte);
                current = tail;""",
       """                bytes.push(byte);
                current = &node.tail;""")
add(f, """            Value::Pair(head, tail) => {
                let Value::Number(number, _) = **head else {""",
       """            Value::Pair(node) => {
                let Value::Number(number, _) = node.head else {""")
add(f, """                bytes.push(number as u8);
                current = tail;""",
       """                bytes.push(number as u8);
                current = &node.tail;""")

# ---------- crates/sens-host/src/native_exec.rs ----------
f = "crates/sens-host/src/native_exec.rs"
add(f, """            Value::Pair(head, tail) => {
                let Some(byte) = machine_byte(head) else {""",
       """            Value::Pair(node) => {
                let Some(byte) = machine_byte(&node.head) else {""")
add(f, """                bytes.push(byte);
                current = tail;""",
       """                bytes.push(byte);
                current = &node.tail;""")

# ---------- crates/sens-host/src/process_raw.rs ----------
f = "crates/sens-host/src/process_raw.rs"
add(f, """            Value::Pair(head, tail) => {
                let Value::String(ref text) = **head else {""",
       """            Value::Pair(node) => {
                let Value::String(ref text) = node.head else {""")
add(f, """                items.push(text.to_string());
                current = tail;""",
       """                items.push(text.to_string());
                current = &node.tail;""")

# ---------- crates/sens-host/src/system_one_model.rs ----------
f = "crates/sens-host/src/system_one_model.rs"
add(f, """            Value::Pair(head, tail) => {
                result.push((**head).clone());
                cursor = tail;
            }""",
       """            Value::Pair(node) => {
                result.push(node.head.clone());
                cursor = &node.tail;
            }""")

# ---------- crates/sens-host/tests/capabilities.rs ----------
f = "crates/sens-host/tests/capabilities.rs"
add(f, """    let Value::Pair(ref exit_code, ref rest) = result.value else {
        panic!("process-run should return a 3-element list");
    };
    assert_eq!(**exit_code, Value::Number(0.0, Exactness::Exact));
    let Value::Pair(ref stdout, _) = **rest else {
        panic!("process-run should return a 3-element list");
    };
    let Value::String(ref stdout) = **stdout else {
        panic!("stdout should be a string");
    };""",
       """    let Value::Pair(ref node) = result.value else {
        panic!("process-run should return a 3-element list");
    };
    assert_eq!(node.head, Value::Number(0.0, Exactness::Exact));
    let Value::Pair(ref rest) = node.tail else {
        panic!("process-run should return a 3-element list");
    };
    let Value::String(ref stdout) = rest.head else {
        panic!("stdout should be a string");
    };""", count=None)

# ---------- crates/sens-lsp/src/protocol.rs ----------
f = "crates/sens-lsp/src/protocol.rs"
add(f, """            Value::Pair(entry, rest) => {
                if let Value::Pair(k, v) = &**entry {
                    if let Value::String(name) = &**k {
                        if name.as_ref() == key {
                            return Some(v);
                        }
                    }
                }
                current = rest;
            }""",
       """            Value::Pair(node) => {
                if let Value::Pair(entry) = &node.head {
                    if let Value::String(name) = &entry.head {
                        if name.as_ref() == key {
                            return Some(&entry.tail);
                        }
                    }
                }
                current = &node.tail;
            }""")
add(f, """            Value::Pair(head, tail) => {
                items.push(&**head);
                current = tail;
            }""",
       """            Value::Pair(node) => {
                items.push(&node.head);
                current = &node.tail;
            }""")

# ---------- tests ----------
f = "crates/sens/tests/codec_in_sens.rs"
add(f, """    let Value::Pair(head, tail) = &result.value else {
        panic!("D2:11 must produce a dotted SENS pair, not a proxy list");
    };
    let Value::DomainIdentity(head) = head.as_ref() else {
        panic!("D3:100 must preserve exact identity");
    };
    let Value::DomainIdentity(tail) = tail.as_ref() else {
        panic!("D3:111 must preserve exact identity");
    };""",
       """    let Value::Pair(node) = &result.value else {
        panic!("D2:11 must produce a dotted SENS pair, not a proxy list");
    };
    let Value::DomainIdentity(head) = &node.head else {
        panic!("D3:100 must preserve exact identity");
    };
    let Value::DomainIdentity(tail) = &node.tail else {
        panic!("D3:111 must preserve exact identity");
    };""")

for f in ["crates/sens/tests/compiler_domain_shape.rs",
          "crates/sens/tests/compiler_nucleus_sens.rs",
          "crates/sens/tests/compiler_role_cutover.rs",
          "crates/wsm-guard-core/src/lib.rs"]:
    add(f, """Value::Pair(head, tail) => {
                out.push(head.as_ref());
                cursor = tail.as_ref();""",
        """Value::Pair(node) => {
                out.push(&node.head);
                cursor = &node.tail;""")

f = "crates/sens/tests/compiler_l1_l5_role.rs"
add(f, """    let Value::Pair(width, rest) = &result else {
        panic!("D3:000 decomposition must be a two-element list, got {result:?}");
    };
    assert!(matches!(
        width.as_ref(),
        Value::Number(value, Exactness::Exact) if *value == 3.0
    ));
    let Value::Pair(bits, tail) = rest.as_ref() else {
        panic!("D3:000 shape bits missing: {rest:?}");
    };
    assert!(matches!(tail.as_ref(), Value::Nil));

    let Value::Pair(bit0, rest) = bits.as_ref() else {
        panic!("D3:000 first bit missing: {bits:?}");
    };
    let Value::Pair(bit1, rest) = rest.as_ref() else {
        panic!("D3:000 second bit missing: {rest:?}");
    };
    let Value::Pair(bit2, tail) = rest.as_ref() else {
        panic!("D3:000 third bit missing: {rest:?}");
    };
    assert!(matches!(tail.as_ref(), Value::Nil));
    assert_eq!(bit0.as_predicate_bit(), Some(false));
    assert_eq!(bit1.as_predicate_bit(), Some(false));
    assert_eq!(bit2.as_predicate_bit(), Some(false));""",
       """    let Value::Pair(node) = &result else {
        panic!("D3:000 decomposition must be a two-element list, got {result:?}");
    };
    assert!(matches!(
        &node.head,
        Value::Number(value, Exactness::Exact) if *value == 3.0
    ));
    let Value::Pair(node) = &node.tail else {
        panic!("D3:000 shape bits missing: {result:?}");
    };
    assert!(matches!(node.tail, Value::Nil));

    let Value::Pair(bit0) = &node.head else {
        panic!("D3:000 first bit missing: {result:?}");
    };
    let Value::Pair(bit1) = &bit0.tail else {
        panic!("D3:000 second bit missing: {result:?}");
    };
    let Value::Pair(bit2) = &bit1.tail else {
        panic!("D3:000 third bit missing: {result:?}");
    };
    assert!(matches!(bit2.tail, Value::Nil));
    assert_eq!(bit0.head.as_predicate_bit(), Some(false));
    assert_eq!(bit1.head.as_predicate_bit(), Some(false));
    assert_eq!(bit2.head.as_predicate_bit(), Some(false));""")

f = "crates/sens/tests/d8_env_reflection_recovery.rs"
add(f, """            Value::Pair(entry, tail) => {
                let Value::Pair(key, value) = entry.as_ref() else {
                    panic!("ENV snapshot entry must be a dotted pair");
                };
                if matches!(key.as_ref(), Value::String(text) if text.as_ref() == name) {
                    return Some(value.as_ref().clone());
                }
                cursor = tail.as_ref();
            }""",
       """            Value::Pair(node) => {
                let Value::Pair(entry) = &node.head else {
                    panic!("ENV snapshot entry must be a dotted pair");
                };
                if matches!(&entry.head, Value::String(text) if text.as_ref() == name) {
                    return Some(entry.tail.clone());
                }
                cursor = &node.tail;
            }""")
add(f, """            Value::Pair(entry, tail) => {
                let Value::Pair(key, _) = entry.as_ref() else {
                    panic!("ENV snapshot entry must be a dotted pair");
                };
                let Value::String(text) = key.as_ref() else {
                    panic!("ENV snapshot key must be a string");
                };
                names.push(text.to_string());
                cursor = tail.as_ref();
            }""",
       """            Value::Pair(node) => {
                let Value::Pair(entry) = &node.head else {
                    panic!("ENV snapshot entry must be a dotted pair");
                };
                let Value::String(text) = &entry.head else {
                    panic!("ENV snapshot key must be a string");
                };
                names.push(text.to_string());
                cursor = &node.tail;
            }""")

f = "crates/sens/tests/exact_domain_public_entry.rs"
add(f, "assert!(matches!(made_list.value, Value::Pair(_, _)));", "assert!(matches!(made_list.value, Value::Pair(_)));")

f = "crates/sens/tests/lisp_fs_d24_revision_cutover.rs"
add(f, "use sens::{eval_program, BinaryNumber, ErrorKind, Session, Value};",
       "use sens::{eval_program, BinaryNumber, ErrorKind, PairNode, Session, Value};")
add(f, "        Value::Pair(Rc::new(head), Rc::new(tail))",
       "        Value::Pair(Rc::new(PairNode { head, tail }))")
add(f, """    let Value::Pair(_, rest) = &snapshot else {
        panic!("snapshot: missing objects");
    };
    let Value::Pair(_, rest) = rest.as_ref() else {
        panic!("snapshot: missing bindings");
    };
    let Value::Pair(revision, tail) = rest.as_ref() else {
        panic!("snapshot: missing revision");
    };
    assert!(
        matches!(tail.as_ref(), Value::Nil),
        "snapshot has extra fields"
    );
    revision.as_ref().clone()""",
       """    let Value::Pair(node) = &snapshot else {
        panic!("snapshot: missing objects");
    };
    let Value::Pair(node) = &node.tail else {
        panic!("snapshot: missing bindings");
    };
    let Value::Pair(node) = &node.tail else {
        panic!("snapshot: missing revision");
    };
    assert!(
        matches!(node.tail, Value::Nil),
        "snapshot has extra fields"
    );
    node.head.clone()""")

f = "crates/sens/tests/math_domain_exclusivity.rs"
add(f, """use sens::{
    eval_parsed_expressions, eval_program, parse_mixed_exact_domain, BinaryNumber,
    BinarySourceWord, Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, Bit9, DomainIdentity,
    ErrorKind, Exactness, Rational, Session, Value,
};""",
       """use sens::{
    eval_parsed_expressions, eval_program, parse_mixed_exact_domain, BinaryNumber,
    BinarySourceWord, Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, Bit9, DomainIdentity,
    ErrorKind, Exactness, PairNode, Rational, Session, Value,
};""")
add(f, """            list = Value::Pair(
                std::rc::Rc::new(Value::Symbol(std::rc::Rc::from("елемент"))),
                std::rc::Rc::new(list),
            );""",
       """            list = Value::Pair(std::rc::Rc::new(PairNode {
                head: Value::Symbol(std::rc::Rc::from("елемент")),
                tail: list,
            }));""")
add(f, """        Value::Pair(
            std::rc::Rc::new(unit.clone()),
            std::rc::Rc::new(Value::Pair(
                std::rc::Rc::new(unit),
                std::rc::Rc::new(Value::Nil),
            )),
        ),""",
       """        Value::Pair(std::rc::Rc::new(PairNode {
            head: unit.clone(),
            tail: Value::Pair(std::rc::Rc::new(PairNode {
                head: unit,
                tail: Value::Nil,
            })),
        })),""")
add(f, """        Value::Pair(
            std::rc::Rc::new(Value::Symbol(std::rc::Rc::from("елемент"))),
            std::rc::Rc::new(Value::Nil),
        ),""",
       """        Value::Pair(std::rc::Rc::new(PairNode {
            head: Value::Symbol(std::rc::Rc::from("елемент")),
            tail: Value::Nil,
        })),""")
add(f, """        list = Value::Pair(
            std::rc::Rc::new(Value::Symbol(std::rc::Rc::from(symbol))),
            std::rc::Rc::new(list),
        );""",
       """        list = Value::Pair(std::rc::Rc::new(PairNode {
            head: Value::Symbol(std::rc::Rc::from(symbol)),
            tail: list,
        }));""")

f = "crates/sens/tests/physical_t5m_execution.rs"
add(f, """        Value::Pair(head, tail)
            if matches!(head.as_ref(), Value::Nil) && matches!(tail.as_ref(), Value::Nil)""",
       """        Value::Pair(node)
            if matches!(node.head, Value::Nil) && matches!(node.tail, Value::Nil)""")

f = "crates/sens/tests/program_data_d24.rs"
add(f, "assert!(matches!(program, Value::Pair(_, _)));", "assert!(matches!(program, Value::Pair(_)));")

f = "crates/sens/tests/stack_safety.rs"
add(f, "use sens::{eval_program, Exactness, Session, Value};",
       "use sens::{eval_program, Exactness, PairNode, Session, Value};")
add(f, "        list = Value::Pair(Rc::new(Value::Nil), Rc::new(list));",
       "        list = Value::Pair(Rc::new(PairNode { head: Value::Nil, tail: list }));", count=None)
add(f, """    let list1 = Value::Pair(
        Rc::new(Value::Number(1.0, Exactness::Exact)),
        Rc::new(tail.clone()),
    );""",
       """    let list1 = Value::Pair(Rc::new(PairNode {
        head: Value::Number(1.0, Exactness::Exact),
        tail: tail.clone(),
    }));""")
add(f, "    let list2 = Value::Pair(Rc::new(Value::Number(2.0, Exactness::Exact)), Rc::new(tail));",
       "    let list2 = Value::Pair(Rc::new(PairNode { head: Value::Number(2.0, Exactness::Exact), tail }));")

f = "crates/sens/tests/text7_canonical_wire.rs"
add(f, """use sens::{
    decode_binary_frame, encode_binary_frame, encode_text7, render_text7, BinaryFrame, Exactness,
    Text7, Text7Layout, Text7WireError, Value,
};""",
       """use sens::{
    decode_binary_frame, encode_binary_frame, encode_text7, render_text7, BinaryFrame, Exactness,
    PairNode, Text7, Text7Layout, Text7WireError, Value,
};""")
add(f, "    let nested_pair = Value::Pair(Rc::new(Value::Text7(text)), Rc::new(Value::Nil));",
       "    let nested_pair = Value::Pair(Rc::new(PairNode { head: Value::Text7(text), tail: Value::Nil }));")

f = "crates/xtask/src/compiler_compile.rs"
add(f, """    let Value::Pair(head, _) = value else {
        return Err("SENS compiler returned a non-list artifact".into());
    };
    let Value::Symbol(schema) = head.as_ref() else {""",
       """    let Value::Pair(node) = value else {
        return Err("SENS compiler returned a non-list artifact".into());
    };
    let Value::Symbol(schema) = &node.head else {""")


errors = []
for path, ops in OPS.items():
    full = ROOT + path
    text = open(full, encoding="utf-8").read()
    for old, new, count in ops:
        n = text.count(old)
        if count is None:
            if n == 0:
                errors.append(f"{path}: NO MATCH for {old[:60]!r}")
                continue
            text = text.replace(old, new)
        else:
            if n != count:
                errors.append(f"{path}: expected {count} got {n} for {old[:70]!r}")
                continue
            text = text.replace(old, new, count)
    open(full, "w", encoding="utf-8").write(text)

if errors:
    print("ERRORS:")
    for e in errors:
        print("  ", e)
    sys.exit(1)
print("ALL OPS APPLIED OK,", sum(len(v) for v in OPS.values()), "edits across", len(OPS), "files")
