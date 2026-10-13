use std::fs;
use std::path::PathBuf;

use sens::{eval_program, load_core_library, Session};

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(relative)
}

fn eval_text(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .expect("scheduler probe must execute")
        .value
        .to_string()
}

#[test]
fn life_1_scheduler_witness_is_lisp_owned() {
    let scheduler =
        fs::read_to_string(repo_file("lib/life-1-scheduler.lisp"))
            .expect("#801 scheduler source must be readable");
    let witness =
        fs::read_to_string(repo_file("tests/fixtures/life-1-scheduler-witness.lisp"))
            .expect("#801 scheduler witness must be readable");

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    eval_program(&scheduler, &mut session).expect("#801 scheduler source must execute");

    // Duplicate pending-invocation dedup is tracked separately in #942.
    let invocation =
        "(pending-invocation (producer datalog)           (trigger (projection-ready prolog-substitutions-to-datalog-facts))           (provenance-ref observation-42)           (priority ordinary)           (semantic-id \"00001100\"))";

    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-field (quote {invocation}) (quote trigger))"
            ),
            &mut session,
        ),
        "(projection-ready prolog-substitutions-to-datalog-facts)"
    );
    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-field (quote {invocation}) (quote provenance-ref))"
            ),
            &mut session,
        ),
        "observation-42"
    );

    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready?                    (quote {invocation})                    (quote ((projection-ready                      prolog-substitutions-to-datalog-facts observation-42))))"
            ),
            &mut session,
        ),
        "present"
    );
    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready?                    (quote {invocation})                    (quote ((projection-ready                      prolog-substitutions-to-datalog-facts observation-99))))"
            ),
            &mut session,
        ),
        "absent"
    );
    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready?                    (quote {invocation})                    (quote ((projection-ready                      different-bridge-contract observation-42))))"
            ),
            &mut session,
        ),
        "absent"
    );

    let selection = eval_text(
        &format!(
            "(life-scheduler-select-ready                (list (quote {invocation}))                (quote ((projection-ready                  prolog-substitutions-to-datalog-facts observation-42))))"
        ),
        &mut session,
    );
    assert!(
        selection.starts_with("(scheduler-selection ready "),
        "unexpected scheduler selection: {selection}"
    );

    assert_eq!(
        eval_text(
            "(life-scheduler-quiescence                (quote ()) (quote ()) (quote no-transition-required))",
            &mut session,
        ),
        "(quiescence-state quiescent)"
    );

    let result =
        eval_program(&witness, &mut session).expect("#801 scheduler witness must execute");
    assert_eq!(
        result.value.to_string(),
        "(life-1-scheduler-witness (status pass) (detail deduplicated-activation-and-quiescence))"
    );
}


#[test]
fn malformed_trigger_is_absent_not_cdr_failure() {
    let scheduler =
        fs::read_to_string(repo_file("lib/life-1-scheduler.lisp"))
            .expect("scheduler source");
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    eval_program(&scheduler, &mut session).expect("scheduler source must execute");

    let malformed =
        "(pending-invocation (producer datalog) (trigger ()) \
          (provenance-ref observation-42) (priority ordinary) \
          (semantic-id \"10101000\"))";

    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready? \
                   (quote {malformed}) \
                   (quote ((projection-ready prolog-substitutions-to-datalog-facts observation-42))))"
            ),
            &mut session,
        ),
        "absent"
    );

    let valid =
        "(pending-invocation (producer datalog) \
          (trigger (projection-ready prolog-substitutions-to-datalog-facts)) \
          (provenance-ref observation-42) (priority ordinary) \
          (semantic-id \"10101000\"))";

    let selection = eval_text(
        &format!(
            "(life-scheduler-select-ready \
               (list (quote {malformed}) (quote {valid})) \
               (quote ((projection-ready prolog-substitutions-to-datalog-facts observation-42))))"
        ),
        &mut session,
    );
    assert!(
        selection.starts_with("(scheduler-selection ready "),
        "malformed pending entry must be skipped: {selection}"
    );
}


/// Exact-domain runtime witness: the real LIFE-1 Lisp definitions, not mocked.
/// The original two identical NOT(ATOM projections) guards meant that a
/// non-empty candidate list could never reach the equality test.
#[test]
fn projection_match_live_first_later_missing_and_empty() {
    use sens::{
        eval_parsed_expressions, eval_pinned_legacy_core_source,
        parse_mixed_exact_domain,
    };

    let mut session = Session::default();
    eval_pinned_legacy_core_source(
        "lib/core.lisp",
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("source-pinned D3/D4 core");

    let production = include_str!("../../../lib/life-1-scheduler.lisp");
    let start = production
        .find("(0011 життя-проєкція-порівняти")
        .expect("real private D4 helper");
    let end = production[start..]
        .find("(0011 life-scheduler-projection-ready?")
        .map(|relative| start + relative)
        .expect("real public projection-match body");
    let source = &production[start..end];
    assert!(source.contains("((010 projections) (001 absent))"));
    assert!(!source.contains("((0100 (010 projections)) (001 absent))"));
    assert!(!source.contains("(001000 (("));
    assert!(source.contains("(життя-проєкція-порівняти expected projections (100 projections))"));
    let definitions = parse_mixed_exact_domain(source)
        .expect("current exact-width D3/D4 definitions");
    assert_eq!(definitions.len(), 2);
    eval_parsed_expressions(&definitions, &mut session)
        .expect("load real LIFE-1 match functions");

    for (argument, expected) in [
        ("()", "absent"),
        ("((projection-ready prolog observation-42))", "present"),
        ("((projection-ready other observation-99) (projection-ready prolog observation-42))", "present"),
        ("((projection-ready other observation-99))", "absent"),
        ("(malformed (projection-ready prolog observation-42))", "present"),
    ] {
        let program = format!(
            "(life-scheduler-projection-match? \
             (001 (projection-ready prolog observation-42)) (001 {argument}))"
        );
        let exprs = parse_mixed_exact_domain(&program)
            .expect("typed SENS quoted-data input");
        let actual = eval_parsed_expressions(&exprs, &mut session)
            .unwrap_or_else(|error| panic!("real LIFE-1 {program}: {error:?}"))
            .value.to_string();
        assert_eq!(actual, expected, "{argument}");
    }
}

/// Exhaustive catalog proof, without installing any new generator or crate.
/// Exact domain identity is (width, bits), not the integer alone; these
/// 2046 catalog entries are NOT all assumed to be executable functions.
#[test]
fn projection_match_exhaustive_2046_domain_widths_and_negative_mutations() {
    use std::collections::HashSet;

    fn verify_one(width: usize, source: &str) -> Result<(usize, usize), String> {
        let records: Vec<_> = source.lines()
            .filter(|line| line.starts_with("  ("))
            .collect();
        let capacity = 1_usize << width;
        if records.len() != capacity {
            return Err(format!("D{width}: expected {capacity}, found {}", records.len()));
        }
        let fields = ["(ук ", "(укр ", "(san ", "(en ", "(LISP ", "(sym "];
        let mut significant_bits = 0;
        for (index, row) in records.iter().enumerate() {
            let word = row[3..].split_ascii_whitespace().next()
                .ok_or_else(|| format!("D{width}: missing code"))?;
            let expected = format!("{index:0width$b}");
            if word != expected || word.len() != width {
                return Err(format!("D{width}: exact-width identity violation at {index}"));
            }
            let mut last = 0;
            for field in fields {
                let at = row.find(field)
                    .ok_or_else(|| format!("D{width}: missing projection {field} at {word}"))?;
                if at < last {
                    return Err(format!("D{width}: projection order violation at {word}"));
                }
                last = at;
            }
            significant_bits += word.len();
        }
        Ok((records.len(), significant_bits))
    }

    let tables: [(usize, &str); 10] = [
        (1, include_str!("../../../lib/domains/d1.lisp")),
        (2, include_str!("../../../lib/domains/d2.lisp")),
        (3, include_str!("../../../lib/domains/d3.lisp")),
        (4, include_str!("../../../lib/domains/d4.lisp")),
        (5, include_str!("../../../lib/domains/d5.lisp")),
        (6, include_str!("../../../lib/domains/d6.lisp")),
        (7, include_str!("../../../lib/domains/d7.lisp")),
        (8, include_str!("../../../lib/domains/d8.lisp")),
        (9, include_str!("../../../lib/domains/d9.lisp")),
        (10, include_str!("../../../lib/domains/d10.lisp")),
    ];
    let mut count = 0;
    let mut bit_count = 0;
    let mut typed = HashSet::new();
    let mut bare_values = HashSet::new();

    for (width, source) in tables {
        let (rows, bits) = verify_one(width, source).expect("ratified 2046 exact coordinate proof");
        count += rows;
        bit_count += bits;
        for index in 0..rows {
            typed.insert((width, index));
            bare_values.insert(index);
        }
    }
    assert_eq!(count, 2046);
    assert_eq!(typed.len(), 2046);
    assert_eq!(bit_count, 18434);
    assert_eq!(bare_values.len(), 1024, "dropping width collapses identities");

    let d10 = include_str!("../../../lib/domains/d10.lisp");
    let truncated = d10.replacen("  (1111111111 ", "  (111111111 ", 1);
    assert_ne!(truncated, d10, "negative W10→W9 mutation must actually apply");
    assert!(verify_one(10, &truncated).is_err());
    let d7 = include_str!("../../../lib/domains/d7.lisp");
    let duplicate = d7.replacen("  (0000000 ", "  (0000001 ", 1);
    assert_ne!(duplicate, d7, "negative D7 duplicate must actually apply");
    assert!(verify_one(7, &duplicate).is_err());
}
