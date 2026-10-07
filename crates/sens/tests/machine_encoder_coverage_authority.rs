use sens::{eval_program, load_core_library, Session, Value};
use std::env;
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn eval(source: &str, session: &mut Session) -> Value {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("coverage witness failed: {source}: {error}"))
        .value
}

fn proper_list(value: &Value) -> Vec<Value> {
    let mut values = Vec::new();
    let mut cursor = value;
    loop {
        match cursor {
            Value::Pair(head, tail) => {
                values.push(head.as_ref().clone());
                cursor = tail.as_ref();
            }
            Value::Nil => return values,
            other => panic!("expected proper list, got {other}"),
        }
    }
}

fn same_pair_key(left: &Value, right: &Value) -> bool {
    let left = proper_list(left);
    let right = proper_list(right);
    left.len() >= 3 && right.len() >= 3 && left[1] == right[1] && left[2] == right[2]
}

#[test]
fn lisp_coverage_row_predicates_are_exact_d1_for_the_full_pinned_corpus() {
    let root = repo_root();
    let previous = env::current_dir().expect("current directory");
    env::set_current_dir(&root).expect("coverage witness must run from repository root");

    let result = std::panic::catch_unwind(|| {
        let mut session = Session::default();
        load_core_library(&mut session).expect("core library loads");

        let generator_path = root.join("lib/machine/encoding/coverage-generator.lisp");
        let generator = fs::read_to_string(&generator_path)
            .unwrap_or_else(|error| panic!("{}: {error}", generator_path.display()));
        eval_program(&generator, &mut session).expect("coverage generator loads");

        eval_program(
            "(def encoder-coverage-committed-form (car (read-all (read-file \"lib/machine/encoding/coverage.lisp\"))))",
            &mut session,
        )
        .expect("committed coverage form loads");

        assert_eq!(
            eval("encoder-coverage-index-valid?", &mut session).as_predicate_bit(),
            Some(true),
            "input authority checks must cross as exact D1"
        );

        let index_rows = proper_list(&eval("encoder-coverage-index-rows", &mut session));
        let partial_rows = proper_list(&eval("encoder-coverage-partials", &mut session));
        let committed_form = proper_list(&eval("encoder-coverage-committed-form", &mut session));
        let coverage_rows = committed_form[3..].to_vec();

        assert_eq!(index_rows.len(), 1176);
        assert_eq!(partial_rows.len(), 122);
        assert_eq!(coverage_rows.len(), index_rows.len());

        let mut partial_index = 0usize;
        for (index, (index_row, coverage_row)) in
            index_rows.iter().zip(coverage_rows.iter()).enumerate()
        {
            let partial_row = partial_rows.get(partial_index);
            let key_matches = partial_row
                .map(|partial| same_pair_key(index_row, partial))
                .unwrap_or(false);

            if let Some(partial) = partial_row {
                let source = format!(
                    "(encoder-coverage-row-key=? (quote {}) (quote {}))",
                    index_row, partial
                );
                let observed = eval(&source, &mut session);
                assert_eq!(
                    observed.as_predicate_bit(),
                    Some(key_matches),
                    "row-key predicate left exact D1 at admitted row {index}: value={observed}"
                );
            }

            let partial_value = if key_matches {
                partial_row.expect("matching partial row")
            } else {
                &Value::Nil
            };
            let source = format!(
                "(encoder-coverage-committed-row-matches? (quote {}) (quote {}) (quote {}))",
                index_row, coverage_row, partial_value
            );
            let observed = eval(&source, &mut session);
            assert_eq!(
                observed.as_predicate_bit(),
                Some(true),
                "committed row predicate failed at admitted row {index}: value={observed}"
            );

            if key_matches {
                partial_index += 1;
            }
        }

        assert_eq!(partial_index, partial_rows.len());

        let projection = eval_program(
            "(encoder-coverage-projection-valid? encoder-coverage-committed-form)",
            &mut session,
        )
        .expect("full Lisp projection validator must execute without carrier errors")
        .value;
        assert_eq!(
            projection.as_predicate_bit(),
            Some(true),
            "full projection validator must return exact D1 YES, got {projection}"
        );
    });

    env::set_current_dir(previous).expect("restore current directory");
    if let Err(payload) = result {
        std::panic::resume_unwind(payload);
    }
}
