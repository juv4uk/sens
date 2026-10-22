//! D11: усі 512 математично похідних CAR/CDR-селекторів як справжні SENS-функції.
//!
//! Без окремого D11 opcode: кожна 11-бітна похідна отримує тільки тимчасове
//! бібліотечне DEFINE у SENS через чинного батька D10 і CAR або CDR.
//! Джерело точних координат і проєкцій — доменна TSV, не семантика host.
//! Усі результати та контрприклади перевіряє справжній eval_program SENS.

use sens::{eval_program, load_core_library, Session};

const SELECTORS: &str =
    include_str!("../../../knowledge/d11/база-доступних-функцій/селектори-512-д11.tsv");

// Семантичний вирок робить сама програма SENS: для правильного результату
// COND коротко замикається на безпечному значенні, для мутанта доходить до
// навмисно невикличного D1 «ні». Rust перевіряє лише успішність виконання.
fn native_self_verdict(session: &mut Session, id: &str, predicate: &str, expected: bool) {
    let program = if expected {
        format!(
            "(за-умовою ({predicate} (як-є так)) ((атом? (як-є ())) (ні)))"
        )
    } else {
        format!(
            "(за-умовою ({predicate} (ні)) ((атом? (як-є ())) (як-є так)))"
        )
    };
    eval_program(&program, session).unwrap_or_else(|error| {
        panic!(
            "test_id={id} layer=SENS input={program} expected=self-verdict-success actual_error={error}"
        )
    });
}

/// Побудова *даних* для незалежного спостереження: для кожного A/D із
/// батьківського Lisp-імені вкладаємо правильний SENS-список.
/// Важливо: Rust не обчислює жоден CAR/CDR результат — усі вибори робить SENS.
fn witness_tree(parent_lisp: &str, marker: &str) -> String {
    let path = parent_lisp
        .strip_prefix('C')
        .and_then(|rest| rest.strip_suffix('R'))
        .expect("точне Lisp-ім'я селектора C...R");
    assert_eq!(path.len(), 8, "D10 має рівно вісім A/D-кроків: {parent_lisp}");

    let mut tree = format!("(список (як-є {marker}))");
    // Обернення послідовності застосувань: зовнішній селектор інвертуємо
    // першим. Жодного host-обчислення значення SENS.
    for operation in path.bytes() {
        tree = match operation {
            b'A' => format!("(сполучити {tree} (як-є ()))"),
            b'D' => format!("(сполучити (як-є опора) {tree})"),
            _ => panic!("test_id=D11-SELECTOR-ALPHABET input={parent_lisp}"),
        };
    }
    tree
}

#[test]
fn d11_all_512_named_derived_selectors_execute_through_d10_in_sens() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");

    let mut count = 0;
    let mut partial_failures = 0usize;
    let mut parent_bits = std::collections::HashSet::new();
    let mut child_bits = std::collections::HashSet::new();
    let mut child_names = std::collections::HashSet::new();
    let mut child_lisp_names = std::collections::HashSet::new();
    let mut branches = [0usize; 2];

    for row in SELECTORS
        .lines()
        .filter(|line| !line.is_empty() && !line.starts_with('#'))
        .skip(1) // заголовок TSV
    {
        let columns: Vec<&str> = row.split('\t').collect();
        assert_eq!(
            columns.len(), 10,
            "test_id=D11-SELECTOR-TSV input={row} expected=10_columns"
        );

        let bits = columns[0];
        let child_name = columns[2];
        let child_en = columns[4];
        let child_lisp = columns[5];
        let parent = columns[6];
        let parent_lisp = columns[7];
        let branch = columns[8];
        let composition = columns[9];
        assert_eq!(bits.len(), 11, "test_id=D11-WIDTH input={bits}");
        assert_eq!(parent.len(), 10, "test_id=D10-WIDTH input={parent}");
        assert_eq!(&bits[..10], parent, "test_id=D11-PARENT input={bits}");
        assert!(child_bits.insert(bits), "test_id=D11-DUP-BITS input={bits}");
        assert!(
            child_names.insert(child_name),
            "test_id=D11-DUP-NAME input={child_name}"
        );
        parent_bits.insert(parent);

        let (carrier, marker, other, suffix_index, name_end) = match branch {
            "A" => ("перше", "ліве", "праве", 0, "-від-перше"),
            "D" => ("решта", "праве", "ліве", 1, "-від-решта"),
            _ => panic!("test_id=D11-SUFFIX input={bits} actual={branch}"),
        };
        assert_eq!(
            &bits[10..], if suffix_index == 0 { "0" } else { "1" },
            "test_id=D11-SUFFIX-BIT input={bits}"
        );
        // Кожен суфікс має єдине математичне прочитання у ВСІХ
        // проєкціях. Просто C...R-форма недостатня: підміна A↔D
        // не повинна проходити навіть за правильного runtime DEFINE.
        let expected_lisp = format!("{}{branch}R", &parent_lisp[..parent_lisp.len() - 1]);
        assert_eq!(
            child_lisp, expected_lisp,
            "test_id=D11-LISP-DERIVATION input={bits} parent={parent_lisp} suffix={branch}"
        );
        assert_eq!(
            child_en,
            child_lisp.to_ascii_lowercase(),
            "test_id=D11-EN-DERIVATION input={bits} lisp={child_lisp}"
        );
        assert_eq!(
            composition,
            if branch == "A" { "p(CAR(x))" } else { "p(CDR(x))" },
            "test_id=D11-COMPOSITION-LAW input={bits} suffix={branch}"
        );
        assert!(
            child_lisp_names.insert(child_lisp),
            "test_id=D11-DUP-LISP input={bits} name={child_lisp}"
        );
        let parent_name = child_name
            .strip_suffix(name_end)
            .unwrap_or_else(|| panic!("test_id=D11-UKR-PARENT input={child_name}"));

        // D11 child is library-defined in SENS by the already existing D10
        // selector and the D3 CAR/CDR. This does NOT admit a direct D11 opcode.
        let define = format!(
            "(визначити {child_name} (функція (вхід) ({parent_name} ({carrier} вхід))))"
        );
        eval_program(&define, &mut session).unwrap_or_else(|error| {
            panic!("test_id=D11-DEFINE-{bits} layer=SENS input={define} actual_error={error}")
        });

        // Parent p has a characteristic asymmetric tree: p(left) = (ліве),
        // p(right) = (праве). The *native* D10 selector chooses the target.
        let left = witness_tree(parent_lisp, "ліве");
        let right = witness_tree(parent_lisp, "праве");
        let input = format!("(сполучити {left} {right})");

        let positive = format!(
            "(тотожне? (перше ({child_name} {input})) (як-є {marker}))"
        );
        native_self_verdict(
            &mut session,
            &format!("D11-SELECTOR-{bits}-POS"),
            &positive,
            true,
        );

        let negative = format!(
            "(тотожне? (перше ({child_name} {input})) (як-є {other}))"
        );
        native_self_verdict(
            &mut session,
            &format!("D11-SELECTOR-{bits}-NEG"),
            &negative,
            false,
        );

        // The owner-ratified parent is called independently, bypassing the
        // new SENS library function, so a wrong binding cannot conceal failure.
        let parent_law = format!(
            "(тотожне? (перше ({parent_name} ({carrier} {input}))) (як-є {marker}))"
        );
        native_self_verdict(
            &mut session,
            &format!("D11-SELECTOR-{bits}-D10-PARENT"),
            &parent_law,
            true,
        );

        // D11 descendant remains a *partial* CAR/CDR composition:
        // failure at the first D3 selector or inside the D10 parent must
        // propagate as Type, never as D1:NO, D3:000 or an invented D11 opcode.
        // All three source programs are executed by the real SENS evaluator.
        for (case, source_arg) in [
            ("atom-at-entry", "(як-є невузол)"),
            ("empty-at-entry", "(як-є ())"),
            ("atom-after-first-step", "(сполучити (як-є невузол) (як-є ()))"),
        ] {
            let source = format!("({child_name} {source_arg})");
            let error = eval_program(&source, &mut session).expect_err(
                "частковий D11 селектор має відхиляти обрив структури"
            );
            assert_eq!(
                error.kind,
                sens::ErrorKind::Type,
                "test_id=D11-SELECTOR-{bits}-PARTIALITY-{case} layer=SENS input={source} expected=Type actual={error}"
            );
            partial_failures += 1;
        }

        count += 1;
        branches[suffix_index] += 1;
    }

    assert_eq!(count, 512, "test_id=D11-SELECTOR-COUNT");
    assert_eq!(partial_failures, 1536, "test_id=D11-SELECTOR-PARTIALITY-COUNT");
    assert_eq!(child_bits.len(), 512, "test_id=D11-SELECTOR-COORDINATES");
    assert_eq!(child_names.len(), 512, "test_id=D11-SELECTOR-SURFACES");
    assert_eq!(child_lisp_names.len(), 512, "test_id=D11-SELECTOR-LISP-UNIQUENESS");
    assert_eq!(parent_bits.len(), 256, "test_id=D11-SELECTOR-PARENTS");
    assert_eq!(branches, [256, 256], "test_id=D11-SELECTOR-BRANCHES");
}
