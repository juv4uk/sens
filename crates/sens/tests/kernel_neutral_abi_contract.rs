//! The kernel-neutral ABI contract, judged against the real C header.
//!
//! `contracts/kernel-neutral-abi-contract.lisp` states what the C table
//! declares. This test is the external witness: it reads
//! `crates/wsm-kernel-c-abi/include/wsm_kernel.h`, parses the numbers out of
//! it, and hands them to the contract as facts. Nothing in the contract may
//! agree with this test by construction, because the facts come from the
//! header and the contract only compares them.
//!
//! Every case here is a negative control as well as the positive one: a
//! contract that cannot fail is not a contract.

use std::collections::BTreeSet;

use sens::{eval_program, load_core_library, parse, Session};

const HEADER: &str = include_str!("../../wsm-kernel-c-abi/include/wsm_kernel.h");
const CONTRACT: &str = include_str!("../../../contracts/kernel-neutral-abi-contract.lisp");

/// The nine codes `contracts/kernel-neutral-abi-contract.lisp` is allowed to
/// call. PRIMITIVE_TABLE in crates/sens/src/eval/canon.rs admits ten
/// mechanisms; the tenth, 00000000, is the empty code and is not a call.
const ADMITTED_CALL_CODES: [&str; 9] = [
    "00000001", "00000010", "00000011", "00000100", "00000101", "00000110", "00000111", "00001000",
    "00001011",
];

struct Header {
    abi_version: u64,
    kinds: Vec<(String, u64)>,
    statuses: Vec<(String, u64)>,
    slots: Vec<String>,
}

fn snake(name: &str) -> String {
    name.trim()
        .trim_start_matches("WSM_KERNEL_")
        .trim_start_matches("WSM_STATUS_")
        .to_ascii_lowercase()
        .replace('_', "-")
}

fn enum_members<'a>(header: &'a str, name: &str) -> Vec<(String, u64)> {
    let body = header
        .split_once(&format!("typedef enum {name} {{"))
        .expect("enum should exist in the header")
        .1
        .split_once("} ")
        .expect("enum should be closed")
        .0;
    body.split(',')
        .filter_map(|entry| {
            let entry = entry.trim();
            let (member, value) = entry.split_once('=')?;
            let value = value.trim().trim_end_matches('u').trim();
            value
                .parse::<u64>()
                .ok()
                .map(|value| (member.trim().to_string(), value))
        })
        .collect()
}

fn read_header() -> Header {
    let abi = header_abi_version();
    Header {
        abi_version: abi,
        kinds: enum_members(HEADER, "WsmKernelKind"),
        statuses: enum_members(HEADER, "WsmStatus"),
        slots: read_slots(),
    }
}

fn header_abi_version() -> u64 {
    HEADER
        .lines()
        .find_map(|line| line.trim().strip_prefix("#define WSM_KERNEL_ABI_VERSION "))
        .expect("the header should declare an ABI version")
        .trim()
        .trim_end_matches("u")
        .parse()
        .expect("the ABI version should be a number")
}

fn read_slots() -> Vec<String> {
    let body = HEADER
        .split_once("typedef struct WsmKernelVTable {")
        .expect("the vtable should exist in the header")
        .1
        .split_once("} WsmKernelVTable;")
        .expect("the vtable should be closed")
        .0;
    let mut slots = Vec::new();
    for line in body.lines() {
        let field = line.trim().trim_end_matches(';').trim();
        // the slot is a function pointer field; abi_version, kernel and
        // context are the table's fixed values beside the slots
        if let Some(ty) = field.split_whitespace().next() {
            if ty.starts_with("Wsm") && ty.ends_with("Fn") {
                slots.push(
                    ty.trim_start_matches("Wsm")
                        .trim_end_matches("Fn")
                        .to_ascii_lowercase(),
                );
            }
        }
    }
    slots
}

impl Header {
    /// The fact list the contract reads, one dotted cell per declared value.
    fn facts(&self, drop: &str, override_slot_count: Option<u64>) -> String {
        let mut cells = Vec::new();
        let mut push = |key: &str, value: u64| {
            if key != drop {
                cells.push(format!("({key} . {value})"));
            }
        };
        push("abi-version", self.abi_version);
        for (member, value) in &self.kinds {
            let key = format!("kind-{}", snake(member));
            push(&key, *value);
        }
        for (member, value) in &self.statuses {
            let key = format!("status-{}", snake(member));
            push(&key, *value);
        }
        let slot_count = override_slot_count.unwrap_or(self.slots.len() as u64);
        push("slot-count", slot_count);
        format!("(00000001 ({}))", cells.join(" "))
    }

    fn keys(&self) -> Vec<String> {
        let mut keys = vec!["abi-version".to_string(), "slot-count".to_string()];
        keys.extend(self.kinds.iter().map(|(m, _)| format!("kind-{}", snake(m))));
        keys.extend(self.statuses.iter().map(|(m, _)| format!("status-{}", snake(m))));
        keys
    }
}

fn report(facts: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(CONTRACT, &mut session).expect("the ABI contract should load");
    let program = format!("(print (kernel-neutral-abi-report {facts}))");
    eval_program(&program, &mut session)
        .expect("the ABI contract report should evaluate")
        .value
        .to_string()
}

#[test]
fn the_header_really_declares_what_the_contract_assumes() {
    let header = read_header();
    assert_eq!(header.abi_version, 2);
    assert_eq!(
        header.slots,
        vec!["start", "exchange", "snapshot", "stop"],
        "the contract is written in table order, so the order is part of the claim"
    );
    assert_eq!(header.kinds.len(), 4, "four rows means four kernel kinds");
    assert_eq!(header.statuses.len(), 5, "OK plus four failure statuses");
    assert!(
        !header.kinds.iter().any(|(m, _)| m == "WSM_KERNEL_UNASSIGNED"),
        "0 is not a WsmKernelKind member, so the contract must not read it as one"
    );
    let abi_version = header.keys();
    assert_eq!(abi_version[0], "abi-version");
}

#[test]
fn the_real_header_satisfies_the_contract() {
    let header = read_header();
    let report = report(&header.facts("", None));
    assert!(
        report.contains("(status pass)"),
        "the real header must satisfy the contract, got: {report}"
    );
}

#[test]
fn a_drifted_code_fails_with_both_values_named() {
    let header = read_header();
    let facts = header.facts("", Some(header.slots.len() as u64));
    // replace one witnessed code with a number the contract does not state
    let drifted = facts.replacen("(kind-prolog . 2)", "(kind-prolog . 9)", 1);
    let report = report(&drifted);
    assert!(report.contains("(status fail)"), "got: {report}");
    assert!(report.contains("code-mismatch"), "got: {report}");
    assert!(report.contains("(header 9)"), "the header value must be named: {report}");
    assert!(report.contains("(contract 2)"), "the contract value must be named: {report}");
}

#[test]
fn a_missing_fact_is_a_failure_and_never_a_pass() {
    let header = read_header();
    for key in header.keys() {
        let report = report(&header.facts(&key, None));
        assert!(
            report.contains("(status fail)"),
            "dropping {key} must fail, got: {report}"
        );
        assert!(
            report.contains("missing-fact"),
            "dropping {key} must say which fact was missing, got: {report}"
        );
    }
}

#[test]
fn a_wrong_slot_count_fails() {
    let header = read_header();
    let report = report(&header.facts("", Some(header.slots.len() as u64 + 1)));
    assert!(report.contains("(status fail)"), "got: {report}");
    assert!(report.contains("slot-count-mismatch"), "got: {report}");
}

#[test]
fn no_facts_at_all_is_a_failure() {
    let report = report("()");
    assert!(report.contains("(status fail)"), "got: {report}");
    assert!(report.contains("missing-fact"), "got: {report}");
}

#[test]
fn the_contract_judges_its_own_claims_clean() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(CONTRACT, &mut session).expect("the ABI contract should load");
    let result = eval_program("(print (kernel-static-clause-failures))", &mut session)
        .expect("the static clause check should evaluate")
        .value
        .to_string();
    assert_eq!(result, "()", "the contract's own claims must be well formed");
}

#[test]
fn the_contract_calls_only_admitted_codes() {
    parse(CONTRACT).expect("the ABI contract must remain valid SENS source");
    let mut heads = BTreeSet::new();
    let bytes: Vec<char> = CONTRACT.chars().collect();
    for (index, ch) in bytes.iter().enumerate() {
        if *ch != '(' {
            continue;
        }
        let head: String = bytes[index + 1..]
            .iter()
            .take_while(|c| c.is_ascii_digit())
            .collect();
        if head.len() == 8 {
            heads.insert(head);
        }
    }
    for head in &heads {
        assert!(
            ADMITTED_CALL_CODES.contains(&head.as_str()),
            "{head} has no admitted callable mechanism in PRIMITIVE_TABLE"
        );
    }
    assert!(
        !heads.is_empty(),
        "the contract should still call something; an empty scan means the scan is broken"
    );
}

#[test]
fn the_contract_never_calls_a_mechanism_by_name() {
    // `list`, `assoc`, `equal?`, `or`, `not?` and `let` have no admitted
    // mechanism by code, so a bare call head would be a dialect habit, not a
    // substrate call. Only data positions may mention them, and only in text.
    for (line_no, line) in CONTRACT.lines().enumerate() {
        let code = line.trim_start();
        if code.starts_with(';') {
            continue;
        }
        for banned in ["(list ", "(assoc ", "(equal? ", "(or ", "(not? ", "(let "] {
            assert!(
                !code.starts_with(banned),
                "line {} calls {banned} by name: {line}",
                line_no + 1
            );
        }
    }
}
