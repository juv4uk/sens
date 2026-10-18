//! Експериментальний, ЯВНО парний вузький зріз математики D5/D24+.
//!
//! `name.lisp` містить допущену українську D5-голову та операнди
//! `#d24:<exact bits>` чи `#d48:<exact bits>`.
//! Фізичний `name.sens` перевозить лише слова через Zig T5M.
//! ПРИМІТКА: сама ширина фізичного слова не надає D24-identity.
//! Домен береться тільки з перевіреного SENS AST парного джерела;
//! байтове/словесне розходження закриває виконання.
//! Це не standalone T5M interpreter і не формат для RATIO.
//!
//! Виклик: sens-math-t5m encode source.lisp
//!         sens-math-t5m eval source.lisp

#[cfg(feature = "zig-transport")]
mod paired {
    use sens::{BinaryNumber, CoreDomainIdentity, Expr, ExprKind, Session, Value};
    use sens_cli::zig_transport::{self, ExactT5Word};
    use std::{env, fs, fs::OpenOptions, io::Write, path::{Path, PathBuf}};

    struct QualifiedMath {
        identity: CoreDomainIdentity,
        arguments: [BinaryNumber; 2],
    }

    /// SENS читач і lowering — єдине джерело семантичної координати.
    /// Строго один бінарний арифметичний виклик; жодних числових coercion.
    fn qualify(source: &str) -> Result<QualifiedMath, String> {
        let forms = sens::parse(source)
            .map_err(|e| format!("SENS reader: {e}"))?;
        let forms = sens::lower_program(&forms);
        let [Expr { kind: ExprKind::DomainCall(identity, args), .. }] = forms.as_slice() else {
            return Err("SENS admission: expected one exact D5 arithmetic call".into());
        };
        if identity.width() != 5
            || !matches!(identity.packed_bits(), 0b01010 | 0b01011 | 0b10110 | 0b10111)
        {
            return Err("SENS admission: no ratified binary D5 arithmetic head".into());
        }
        let [Expr { kind: ExprKind::BinaryNumber(left), .. },
             Expr { kind: ExprKind::BinaryNumber(right), .. }] = args.as_ref() else {
            return Err("SENS admission: two explicitly D24+-qualified operands required".into());
        };
        let Some(width) = left.numeric_domain_width() else {
            return Err("SENS admission: left operand lacks D24+ identity".into());
        };
        if right.numeric_domain_width() != Some(width) {
            return Err("SENS admission: mixed numeric domains forbidden".into());
        }
        Ok(QualifiedMath {
            identity: *identity,
            arguments: [left.clone(), right.clone()],
        })
    }

    fn word(width: usize, bits: Vec<u8>) -> Result<ExactT5Word, String> {
        ExactT5Word::new(width, bits)
    }

    /// D2 open, EXACT admitted D5 head, two EXACT qualified operands, D2 close.
    /// Zig supplies physical coding only; these widths are word boundaries.
    fn expected_words(program: &QualifiedMath) -> Result<Vec<ExactT5Word>, String> {
        let mut words = vec![
            word(2, vec![1, 0])?,
            word(5, (0..5).rev()
                .map(|shift| ((program.identity.packed_bits() >> shift) & 1) as u8)
                .collect())?,
        ];
        for number in &program.arguments {
            let width = number.numeric_domain_width()
                .ok_or("SENS admission: unqualified number")?;
            let bits = number.exact_numeric_domain_bits()
                .ok_or("SENS admission: missing exact domain word")?;
            words.push(word(width, bits)?);
        }
        words.push(word(2, vec![0, 1])?);
        Ok(words)
    }

    fn eval_verified(source: &str, physical: &[u8]) -> Result<Value, String> {
        let admitted = qualify(source)?;
        let expected = expected_words(&admitted)?;
        // Zig decodes all physical widths; never use legacy BE3 W1–W9.
        let actual = zig_transport::decode_t5_exact_words(physical)?;
        if actual != expected {
            return Err(format!(
                "T5M_PAIR_MISMATCH layer=transport expected_words={} actual_words={}; \
                 source domain admission never follows physical width alone",
                expected.len(), actual.len()
            ));
        }
        // Rehydrate from the *restored physical bits*, with numeric-domain
        // authority carried separately by the verified SENS source AST.
        let mut arguments = Vec::with_capacity(2);
        for (source_number, restored) in admitted.arguments.iter().zip(&actual[2..4]) {
            let domain = source_number.numeric_domain_width()
                .ok_or("SENS admission: missing source numeric identity")?;
            if restored.width != domain {
                return Err("T5M_PAIR_MISMATCH layer=domain width".into());
            }
            let numeric = BinaryNumber::from_numeric_domain_bits(domain, &restored.bits)
                .ok_or("SENS admission: invalid exact numeric word")?;
            arguments.push(Expr {
                kind: ExprKind::BinaryNumber(numeric),
                span: Default::default(),
            });
        }
        let program = [Expr {
            kind: ExprKind::DomainCall(admitted.identity, arguments.into()),
            span: Default::default(),
        }];
        let result = sens::eval_parsed_expressions(&program, &mut Session::default())
            .map_err(|e| format!("SENS eval: {e}"))?;
        Ok(result.value)
    }

    fn sibling(path: &Path) -> Result<PathBuf, String> {
        if path.extension().and_then(|e| e.to_str()) != Some("lisp") {
            return Err("required explicitly qualified .lisp source companion".into());
        }
        Ok(path.with_extension("sens"))
    }

    fn run(args: &[String]) -> Result<(), String> {
        let [action, filename] = args else {
            return Err("usage: sens-math-t5m (encode|eval) source.lisp".into());
        };
        let path = Path::new(filename);
        let physical_path = sibling(path)?;
        let source = fs::read_to_string(path).map_err(|e| format!("read Lisp companion: {e}"))?;
        match action.as_str() {
            "encode" => {
                let admitted = qualify(&source)?;
                let expected = expected_words(&admitted)?;
                let physical = zig_transport::encode_t5_exact_words(&expected)?;
                // Verify the same pair before publishing physical data.
                eval_verified(&source, &physical)?;
                let mut output = OpenOptions::new().write(true).create_new(true)
                    .open(&physical_path).map_err(|e| format!("create .sens (never overwrite): {e}"))?;
                output.write_all(&physical).map_err(|e| format!("write physical T5M: {e}"))?;
                println!("T5M_PAIR_ENCODED physical_bytes={} words={}", physical.len(), expected.len());
                Ok(())
            }
            "eval" => {
                let physical = fs::read(&physical_path)
                    .map_err(|e| format!("read physical T5M: {e}"))?;
                let value = eval_verified(&source, &physical)?;
                println!("{value}");
                Ok(())
            }
            _ => Err("only explicit encode/eval commands are admitted".into()),
        }
    }

    pub fn main() {
        let args: Vec<_> = env::args().skip(1).collect();
        if let Err(error) = run(&args) {
            eprintln!("{error}");
            std::process::exit(1);
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        fn bits(value: i64) -> String {
            format!("{:024b}", (value as i128 & ((1i128 << 24) - 1)))
        }

        fn source(op: &str, left: i64, right: i64) -> String {
            format!("({op} #d24:{} #d24:{})", bits(left), bits(right))
        }

        #[test]
        fn physical_t5m_restores_d24_and_executes_only_with_explicit_sens_admission() {
            for (id, source, expected_width, expected_human) in [
                ("sum", source("додати", 1, 2), 24, "3"),
                ("negative", source("відняти", 1, 3), 24, "-2"),
                ("promote", source("додати", 8_388_607, 1), 48, "8388608"),
                ("product", source("помножити", 7, 6), 24, "42"),
            ] {
                let qualified = qualify(&source).expect("ratified D5 and D24 source");
                let words = expected_words(&qualified).unwrap();
                let physical = zig_transport::encode_t5_exact_words(&words)
                    .expect("real Zig T5M egress");
                let restored = zig_transport::decode_t5_exact_words(&physical)
                    .expect("real Zig T5M ingress");
                assert_eq!(words, restored, "id={id} layer=transport");
                let result = eval_verified(&source, &physical)
                    .unwrap_or_else(|error| panic!("id={id} layer=eval {error}"));
                let Value::BinaryNumber(number) = result else {
                    panic!("id={id} layer=eval expected=D{expected_width}");
                };
                assert_eq!(number.numeric_domain_width(), Some(expected_width), "id={id}");
                assert_eq!(number.to_decimal_string(), expected_human, "id={id}");
            }
        }

        #[test]
        fn t5m_delivers_division_operands_but_sens_alone_creates_exact_ratio() {
            // D5:10111 is the current owner-ratified QUOTIENT, surface «частка».
            // The physical T5M words are two D24 integers, never a flat fraction.
            let source = source("частка", 1, 3);
            let words = expected_words(&qualify(&source).unwrap()).unwrap();
            let physical = zig_transport::encode_t5_exact_words(&words).unwrap();
            let value = eval_verified(&source, &physical)
                .expect("SENS exact division must form canonical reduced RATIO");
            assert!(matches!(value, Value::NumericComposition(_)),
                "test_id=one-third layer=eval expected=canonical-rational");

            let zero_source = source("частка", 1, 0);
            let zero_words = expected_words(&qualify(&zero_source).unwrap()).unwrap();
            let zero_physical = zig_transport::encode_t5_exact_words(&zero_words).unwrap();
            let error = eval_verified(&zero_source, &zero_physical)
                .expect_err("SENS must reject division by D24 zero");
            assert!(error.contains("SENS eval:"),
                "test_id=divide-by-zero layer=eval expected=rejection actual={error}");
        }

        #[test]
        fn physical_t5m_cannot_invent_numeric_admission_or_mutate_exact_bits() {
            for invalid in [
                "(додати 1 2)",
                "(додати #d24:000000000000000000000001 2)",
                "(додати #d24:000000000000000000000001 #d48:000000000000000000000000000000000000000000000010)",
                "(quote #d24:000000000000000000000001)",
            ] {
                assert!(qualify(invalid).is_err(), "unadmitted source={invalid}");
            }
            let admitted = source("додати", 1, 2);
            let words = expected_words(&qualify(&admitted).unwrap()).unwrap();
            let mut altered = words.clone();
            altered[3].bits[23] ^= 1;
            let alien = zig_transport::encode_t5_exact_words(&altered)
                .expect("valid but wrong T5M data");
            assert!(eval_verified(&admitted, &alien).unwrap_err().contains("T5M_PAIR_MISMATCH"));

            // Exactly equal bare 24-bit payload does NOT carry proof of
            // source identity: without its Lisp companion, this is not runnable.
            let bare = zig_transport::encode_t5_exact_words(&[words[2].clone()]).unwrap();
            assert!(eval_verified(&admitted, &bare).unwrap_err().contains("T5M_PAIR_MISMATCH"));
        }
    }
}

#[cfg(feature = "zig-transport")]
fn main() { paired::main(); }

#[cfg(not(feature = "zig-transport"))]
fn main() {
    eprintln!("RUST_ZIG_ONLY: physical T5M paired execution requires Zig");
    std::process::exit(2);
}
