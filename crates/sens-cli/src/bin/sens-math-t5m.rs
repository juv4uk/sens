//! Експериментальний, ЯВНО парний вузький зріз математики D5/D12+.
//!
//! `name.lisp` містить українську D5-голову та десяткові цілі операнди.
//! Адаптер формує exact D12+ до фізичного Zig T5M без host-float.
//! Машинні #d/#b/#q2 літерали не є людською виконуваною поверхнею.
//! Фізичний `name.sens` перевозить лише слова через Zig T5M.
//! ПРИМІТКА: сама ширина фізичного слова не надає числової D12+-тотожності.
//! Домен береться тільки з перевіреного SENS AST парного джерела;
//! байтове/словесне розходження закриває виконання.
//! Це не standalone T5M interpreter і не фізичний формат результату RATIO.
//! Вкладені D5-вирази з точними D12+ листками дозволені.
//! Одномісні D5:01011 і D5:10111 допускаються за чинним законом SENS.
//!
//! Виклик: sens-math-t5m encode source.lisp
//!         sens-math-t5m eval source.lisp

#[cfg(feature = "zig-transport")]
mod paired {
    use sens::{BinaryNumber, Expr, ExprKind, Session, Value};
    use sens_cli::zig_transport::{self, ExactT5MWord};
    use std::{
        env, fs,
        fs::OpenOptions,
        io::Write,
        path::{Path, PathBuf},
    };

    // The physical codec supplies widths and bits, never semantic admission.
    // D5 heads and D12+ leaf identity are selected by SENS lowering alone.
    fn admit(expr: &Expr, depth: usize) -> Result<(), String> {
        if depth > 64 {
            return Err("SENS admission: nested arithmetic exceeds depth limit".into());
        }
        match &expr.kind {
            ExprKind::BinaryNumber(value) if value.numeric_domain_width().is_some() => Ok(()),
            ExprKind::DomainCall(identity, args)
                if identity.width() == 5
                    // Arity is part of the physical admission law: a head is
                    // admitted only for the exact argument counts its D5 law
                    // defines. ZEROP and NUMBERP are strictly unary D5 laws;
                    // DIFFERENCE and QUOTIENT retain their existing unary
                    // forms alongside the binary form; ADD, MULTIPLY, LESS
                    // and GREATER are strictly binary.
                    && match identity.packed_bits() {
                        0b01000 | 0b01001 => args.len() == 1,
                        0b01011 | 0b10111 => args.len() == 1 || args.len() == 2,
                        0b01010 | 0b10110 | 0b11010 | 0b11011 => args.len() == 2,
                        _ => false,
                    } =>
            {
                // Atomic binary operands must carry the SAME admitted Dn.
                // Nested results (possibly widened by an earlier operation)
                // remain SENS evaluator authority, not host coercion.
                if args.len() == 2 {
                    if let (ExprKind::BinaryNumber(left), ExprKind::BinaryNumber(right)) =
                        (&args[0].kind, &args[1].kind)
                    {
                        if left.numeric_domain_width() != right.numeric_domain_width() {
                            return Err("SENS admission: mixed numeric domains are forbidden".into());
                        }
                    }
                }
                for arg in args.iter() { admit(arg, depth + 1)?; }
                Ok(())
            }
            _ => Err(format!(
                "SENS admission: only qualified D12+ atoms and admitted binary D5 math/predicate calls; actual={:?}",
                expr.kind
            )),
        }
    }

    fn qualify(source: &str) -> Result<Expr, String> {
        // The paired math/T5M executable surface starts source integers at D12.
        qualify_with_minimum_width(source, 12)
    }

    // D12/T5M source admits signed decimal INTEGER lexemes only.
    // The human REPL may parse exact rationals (including Ukrainian comma
    // decimals and exponent notation), but those values must not cross this
    // integer-only physical operand boundary as if they were D12 words.
    fn contains_non_integer_numeric_lexeme(expr: &Expr, source: &str) -> bool {
        fn integer_token(token: &str) -> bool {
            let digits = token
                .strip_prefix('-')
                .or_else(|| token.strip_prefix('+'))
                .unwrap_or(token);
            !digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit())
        }

        fn numeric_fractional_spelling(expr: &Expr, source: &str) -> bool {
            // The general SENS REPL accepts exact decimal/exponent literals,
            // but this physical D12/T5M profile is deliberately integer-only.
            // Check the original source spelling even when the reader leaves a
            // numeric-looking token as Symbol (for example 0,5 under a
            // surface-specific read path). Otherwise the general REPL
            // projection can silently turn it into a D5 quotient call.
            let Some(token) = source.get(expr.span.start..expr.span.end) else {
                return false;
            };
            let unsigned = token
                .strip_prefix('-')
                .or_else(|| token.strip_prefix('+'))
                .unwrap_or(token);
            let starts_with_digit = unsigned
                .as_bytes()
                .first()
                .is_some_and(u8::is_ascii_digit);
            let comma_prefixed_digits = unsigned
                .strip_prefix(',')
                .is_some_and(|digits| {
                    !digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit())
                });
            let has_fractional_marker = unsigned
                .bytes()
                .any(|byte| matches!(byte, b',' | b'.' | b'e' | b'E'))
                || unsigned.contains('е')
                || unsigned.contains('Е');
            (starts_with_digit || comma_prefixed_digits)
                && has_fractional_marker
                && !integer_token(token)
        }

        // Validate the source lexeme before the REPL projection can normalize
        // an exact decimal into D5 QUOTIENT over D12+ components.
        if numeric_fractional_spelling(expr, source) {
            return true;
        }

        match &expr.kind {
            ExprKind::Rational(_) | ExprKind::Number(_, _) => {
                let Some(token) = source.get(expr.span.start..expr.span.end) else {
                    return true;
                };
                !integer_token(token)
            }
            ExprKind::List(items)
            | ExprKind::Call(_, items)
            | ExprKind::DomainCall(_, items) => items
                .iter()
                .any(|item| contains_non_integer_numeric_lexeme(item, source)),
            ExprKind::Pair(left, right) => {
                contains_non_integer_numeric_lexeme(left, source)
                    || contains_non_integer_numeric_lexeme(right, source)
            }
            _ => false,
        }
    }

    fn qualify_with_minimum_width(
        source: &str,
        minimum_width: usize,
    ) -> Result<Expr, String> {
        // Вхід — людський Lisp; encoded literals cannot grant numeric identity.
        if source.lines().any(|line| {
            let code = line.split(';').next().unwrap_or("");
            ["#d", "#b", "#q2"].iter().any(|tag| code.contains(*tag))
        }) {
            return Err("SENS admission: encoded literals forbidden in executable Lisp".into());
        }
        let parsed = sens::parse(source).map_err(|error| format!("SENS reader: {error}"))?;
        if parsed.iter().any(|expr| contains_non_integer_numeric_lexeme(expr, source)) {
            return Err(
                "SENS admission: the D12/T5M operand profile accepts signed decimal integers only; exact rationals remain REPL values"
                    .into(),
            );
        }
        // The SENS source projector owns numeric width selection; transport only
        // preserves the resulting explicit width and bits.
        let projected =
            sens::source_projection::project_ukr_decimal_integer_literals_with_minimum_width(
                &parsed,
                source,
                minimum_width,
            )
            .map_err(|error| format!("SENS decimal source: {error}"))?;
        let lowered = sens::lower_program(&projected);
        let [root] = lowered.as_slice() else {
            return Err("SENS admission: expected exactly one mathematical form".into());
        };
        if !matches!(&root.kind, ExprKind::DomainCall(_, _)) {
            return Err("SENS admission: bare numeric data is not executable".into());
        }
        admit(root, 0)?;
        Ok(root.clone())
    }

    fn word(width: usize, bits: Vec<u8>) -> Result<ExactT5MWord, String> {
        ExactT5MWord::new(width, bits)
    }

    // Existing D2 OPEN / D5 function / subexpressions / D2 CLOSE.
    // The T5M word schema and physical encoder remain unchanged.
    fn append_words(expr: &Expr, out: &mut Vec<ExactT5MWord>) -> Result<(), String> {
        match &expr.kind {
            ExprKind::BinaryNumber(number) => {
                let width = number
                    .numeric_domain_width()
                    .ok_or("SENS admission: unqualified numeric leaf")?;
                out.push(word(
                    width,
                    number
                        .exact_numeric_domain_bits()
                        .ok_or("SENS admission: missing numeric exact bits")?,
                )?);
            }
            ExprKind::DomainCall(identity, args) => {
                out.push(word(2, vec![1, 0])?);
                out.push(word(
                    5,
                    (0..5)
                        .rev()
                        .map(|n| ((identity.packed_bits() >> n) & 1) as u8)
                        .collect(),
                )?);
                for arg in args.iter() {
                    append_words(arg, out)?;
                }
                out.push(word(2, vec![0, 1])?);
            }
            _ => return Err("SENS admission: non-numeric AST".into()),
        }
        Ok(())
    }

    fn expected_words(root: &Expr) -> Result<Vec<ExactT5MWord>, String> {
        admit(root, 0)?;
        let mut out = Vec::new();
        append_words(root, &mut out)?;
        Ok(out)
    }

    // Each numeric leaf is reconstructed FROM the actual Zig-restored bits.
    // The separately-validated source AST grants D5/D12+ identity and structure.
    fn reconstruct(
        source: &Expr,
        physical: &[ExactT5MWord],
        cursor: &mut usize,
    ) -> Result<Expr, String> {
        let kind = match &source.kind {
            ExprKind::BinaryNumber(number) => {
                let width = number
                    .numeric_domain_width()
                    .ok_or("SENS admission: missing numeric domain")?;
                let word = physical
                    .get(*cursor)
                    .ok_or("T5M_PAIR_MISMATCH: numeric leaf absent")?;
                *cursor += 1;
                if word.width != width {
                    return Err("T5M_PAIR_MISMATCH: different domain width".into());
                }
                ExprKind::BinaryNumber(
                    BinaryNumber::from_numeric_domain_bits(width, &word.bits)
                        .ok_or("SENS admission: invalid exact numeric bits")?,
                )
            }
            ExprKind::DomainCall(identity, args) => {
                if physical.get(*cursor + 1).is_none() {
                    return Err("T5M_PAIR_MISMATCH: missing call head".into());
                }
                *cursor += 2; // D2 OPEN and exact D5 head already compared
                let mut children = Vec::with_capacity(args.len());
                for arg in args.iter() {
                    children.push(reconstruct(arg, physical, cursor)?);
                }
                if physical.get(*cursor).is_none() {
                    return Err("T5M_PAIR_MISMATCH: missing D2 CLOSE".into());
                }
                *cursor += 1;
                ExprKind::DomainCall(*identity, children.into())
            }
            _ => return Err("SENS admission: cannot reconstruct this AST".into()),
        };
        Ok(Expr {
            kind,
            span: source.span,
        })
    }

    fn eval_verified(source: &str, physical: &[u8]) -> Result<Value, String> {
        let qualified = qualify(source)?;
        let expected = expected_words(&qualified)?;
        // Only Zig physically encodes or decodes T5M; no W1–W9 truncation.
        let restored = zig_transport::decode_t5m_exact_words(physical)?;
        if restored != expected {
            let index = restored.iter().zip(&expected).position(|(a, b)| a != b);
            return Err(format!(
                "T5M_PAIR_MISMATCH layer=transport index={index:?} expected_words={} actual_words={}; domain cannot be inferred from width",
                expected.len(), restored.len()
            ));
        }
        let mut cursor = 0usize;
        let expr = reconstruct(&qualified, &restored, &mut cursor)?;
        if cursor != restored.len() {
            return Err("T5M_PAIR_MISMATCH: trailing exact physical words".into());
        }
        sens::eval_parsed_expressions(&[expr], &mut Session::default())
            .map(|result| result.value)
            .map_err(|e| format!("SENS eval: {e}"))
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
                let physical = zig_transport::encode_t5m_exact_words(&expected)?;
                // Verify the same pair before publishing physical data.
                eval_verified(&source, &physical)?;
                let mut output = OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(&physical_path)
                    .map_err(|e| format!("create .sens (never overwrite): {e}"))?;
                output
                    .write_all(&physical)
                    .map_err(|e| format!("write physical T5M: {e}"))?;
                println!(
                    "T5M_PAIR_ENCODED physical_bytes={} words={}",
                    physical.len(),
                    expected.len()
                );
                Ok(())
            }
            "eval" => {
                let physical =
                    fs::read(&physical_path).map_err(|e| format!("read physical T5M: {e}"))?;
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

        fn source(op: &str, left: i64, right: i64) -> String {
            format!("({op} {left} {right})")
        }

        #[test]
        fn d12_first_numeric_predicate_transport_preserves_sens_results() {
            // SENS owns each predicate. This transport test proves that the
            // explicit D12-first projection and Zig/T5M preserve the result;
            // decimal boundary values stay test inputs here, not executable
            // Lisp literals that would bypass the source-domain guard.
            let check = |id: &str, text: &str, expected: bool, min_d12_operands: usize| {
                let admitted = qualify(text)
                    .unwrap_or_else(|error| panic!("id={id} layer=SENS-source {error}"));
                let words = expected_words(&admitted)
                    .unwrap_or_else(|error| panic!("id={id} layer=SENS-admission {error}"));
                let d12_operands = words.iter().filter(|word| word.width == 12).count();
                assert!(
                    d12_operands >= min_d12_operands,
                    "id={id} layer=projection expected_at_least_D12_operands={min_d12_operands} actual={d12_operands}"
                );
                let physical = zig_transport::encode_t5m_exact_words(&words)
                    .unwrap_or_else(|error| panic!("id={id} layer=Zig-T5M encode {error}"));
                let restored = zig_transport::decode_t5m_exact_words(&physical)
                    .unwrap_or_else(|error| panic!("id={id} layer=Zig-T5M decode {error}"));
                assert_eq!(restored, words, "id={id} layer=physical-roundtrip");
                let actual = eval_verified(text, &physical)
                    .unwrap_or_else(|error| panic!("id={id} layer=SENS-eval {error}"));
                assert_eq!(
                    actual.as_predicate_bit(),
                    Some(expected),
                    "id={id} layer=SENS-law expected={} actual={actual}",
                    if expected { "D1:так" } else { "D1:ні" }
                );
            };

            // Canonical Lisp witnesses remain the authority for the two positive laws.
            for (id, fixture) in [
                ("d5-d12-zerop", "d5-d12-zerop-law.lisp"),
                ("d5-d12-numberp-ratio", "d5-d12-numberp-law.lisp"),
            ] {
                let source_path = Path::new(env!("CARGO_MANIFEST_DIR"))
                    .join("../../tests/semantic")
                    .join(fixture);
                let text = std::fs::read_to_string(&source_path).unwrap_or_else(|error| {
                    panic!("id={id} fixture={} error={error}", source_path.display())
                });
                check(id, &text, true, 2);
            }

            // Boundary probes are test-driver inputs, not checked-in executable Lisp.
            check("d5-d12-zerop-negative-limit", "(нуль? -2048)", false, 1);
            check("d5-d12-zerop-promoted-nonzero", "(нуль? (додати 2047 1))", false, 2);
        }

        #[test]
        fn physical_t5m_restores_exact_d12plus_words_with_explicit_sens_admission() {
            for (id, source, expected_width, expected_human) in [
                ("sum", source("додати", 1, 2), 12, "3"),
                ("negative", source("відняти", 1, 3), 12, "-2"),
                ("promote", source("додати", 8_388_607, 1), 48, "8388608"),
                ("product", source("помножити", 7, 6), 12, "42"),
            ] {
                let qualified = qualify(&source).expect("ratified D5 and D12+ source");
                let words = expected_words(&qualified).unwrap();
                let physical =
                    zig_transport::encode_t5m_exact_words(&words).expect("real Zig T5M egress");
                let restored =
                    zig_transport::decode_t5m_exact_words(&physical).expect("real Zig T5M ingress");
                assert_eq!(words, restored, "id={id} layer=transport");
                let result = eval_verified(&source, &physical)
                    .unwrap_or_else(|error| panic!("id={id} layer=eval {error}"));
                let Value::BinaryNumber(ref number) = result else {
                    panic!("id={id} layer=eval expected=D{expected_width}");
                };
                assert_eq!(
                    number.numeric_domain_width(),
                    Some(expected_width),
                    "id={id}"
                );
                assert_eq!(number.to_decimal_string(), expected_human, "id={id}");
            }
        }

        #[test]
        fn decimal_ukrainian_lisp_through_physical_zig_t5m_and_sens_math() {
            for (id, text, input_width, expected) in [
                ("sum", "(додати 1 2)", 12, "3"),
                ("negative", "(відняти 1 3)", 12, "-2"),
                ("signed", "(додати -3 1)", 12, "-2"),
                ("carry", "(додати 8388607 1)", 24, "8388608"),
                ("wide", "(додати 8388608 1)", 48, "8388609"),
                ("wide-reverse", "(додати 1 8388608)", 48, "8388609"),
                ("product", "(помножити 7 6)", 12, "42"),
            ] {
                let words = expected_words(&qualify(text).unwrap()).unwrap();
                assert_eq!(words[2].width, input_width, "test_id={id} layer=source");
                let packed = zig_transport::encode_t5m_exact_words(&words).unwrap();
                assert_eq!(
                    zig_transport::decode_t5m_exact_words(&packed).unwrap(),
                    words
                );
                let got = eval_verified(text, &packed).unwrap();
                assert_eq!(got.to_string(), expected, "test_id={id} layer=SENS");
            }
            // Нова реальність: D12-first source profile widens exactly through D24+,
            // тож 2^127 — законне точне ціле, а не «завеликий» літерал. Невалідними
            // лишаються десяткові дроби, експоненти, хибна арність і не-число.
            for invalid in [
                "(додати 0,5 2)",
                "(додати 1e2 2)",
                "(додати 1 2 3)",
                "(як-є 1)",
            ] {
                assert!(
                    qualify(invalid).is_err(),
                    "test_id=invalid-math-source layer=SENS actual={invalid}"
                );
            }
        }

        #[test]
        fn d12_edges_roundtrip_and_grow_through_zig_t5m_and_sens_math() {
            for (id, text, input_width, output_width, expected) in [
                ("positive-overflow", "(додати 2047 1)", 12, 24, "2048"),
                ("negative-overflow", "(додати -2048 -1)", 12, 24, "-2049"),
                ("signed-cancellation", "(додати -2048 2047)", 12, 12, "-1"),
            ] {
                let words = expected_words(&qualify(text).unwrap()).unwrap();
                assert_eq!(words[2].width, input_width, "id={id} layer=source");
                let physical = zig_transport::encode_t5m_exact_words(&words)
                    .unwrap_or_else(|error| panic!("id={id} layer=Zig-T5M encode {error}"));
                assert_eq!(
                    zig_transport::decode_t5m_exact_words(&physical).unwrap(),
                    words,
                    "id={id} layer=Zig-T5M roundtrip"
                );
                let result = eval_verified(text, &physical)
                    .unwrap_or_else(|error| panic!("id={id} layer=SENS {error}"));
                let Value::BinaryNumber(ref number) = result else {
                    panic!("id={id} layer=SENS expected exact D{output_width} integer");
                };
                assert_eq!(number.numeric_domain_width(), Some(output_width), "id={id}");
                assert_eq!(number.to_decimal_string(), expected, "id={id}");
            }

            // Негативний фізичний свідок: шлях D12 передає обидва операнди,
            // але SENS мусить відхилити ділення на доменний нуль.
            let text = "(частка 1 0)";
            let words = expected_words(&qualify(text).unwrap()).unwrap();
            assert_eq!(words[2].width, 12, "id=d12-zero-division layer=source");
            assert_eq!(words[3].width, 12, "id=d12-zero-division layer=source");
            let physical = zig_transport::encode_t5m_exact_words(&words).unwrap();
            let error = eval_verified(text, &physical)
                .expect_err("D12 division by zero must fail in SENS after T5M roundtrip");
            assert!(
                error.contains("SENS eval:"),
                "id=d12-zero-division layer=SENS error={error}"
            );
        }

        #[test]
        fn t5m_delivers_division_operands_but_sens_alone_creates_exact_ratio() {
            // D5:10111 is the current owner-ratified QUOTIENT, surface «частка».
            // The physical T5M words are two exact D12 integers, never a flat fraction.
            let source_expr = source("частка", 1, 3);
            let words = expected_words(&qualify(&source_expr).unwrap()).unwrap();
            let physical = zig_transport::encode_t5m_exact_words(&words).unwrap();
            let value = eval_verified(&source_expr, &physical)
                .expect("SENS exact division must form canonical reduced RATIO");
            assert!(
                matches!(value, Value::NumericComposition(_)),
                "test_id=one-third layer=eval expected=canonical-rational"
            );

            let zero_source = source("частка", 1, 0);
            let zero_words = expected_words(&qualify(&zero_source).unwrap()).unwrap();
            let zero_physical = zig_transport::encode_t5m_exact_words(&zero_words).unwrap();
            let error = eval_verified(&zero_source, &zero_physical)
                .expect_err("SENS must reject division by D12 zero");
            assert!(
                error.contains("SENS eval:"),
                "test_id=divide-by-zero layer=eval expected=rejection actual={error}"
            );
        }

        #[test]
        fn nested_d5_ratios_are_exact_through_zig_t5m_and_sens() {
            // Three D5 calls (9 control words) plus four exact D12 leaves.
            let nested = format!(
                "(додати {} {})",
                source("частка", 1, 2),
                source("частка", 1, 3),
            );
            let root = qualify(&nested).expect("ratified nested math");
            let words = expected_words(&root).unwrap();
            assert_eq!(words.len(), 13, "three D5 applications and four D12 leaves");
            let bytes = zig_transport::encode_t5m_exact_words(&words).unwrap();
            assert_eq!(
                zig_transport::decode_t5m_exact_words(&bytes).unwrap(),
                words
            );
            let actual = eval_verified(&nested, &bytes).unwrap();
            assert!(
                matches!(actual, Value::NumericComposition(_)),
                "test_id=ratio-sum layer=eval expected=reduced-RATIO"
            );
            let oracle_source = source("частка", 5, 6);
            let oracle_parsed =
                sens::parse(&oracle_source).expect("independent SENS source parses");
            let oracle_projected =
                sens::source_projection::project_ukr_decimal_integer_literals_with_minimum_width(
                    &oracle_parsed,
                    &oracle_source,
                    12,
                )
                .expect("independent SENS oracle uses the same explicit D12 profile");
            let expected = sens::eval_parsed_expressions(
                &oracle_projected,
                &mut Session::default(),
            )
            .expect("independent SENS arithmetic oracle")
            .value;
            assert_eq!(actual, expected, "test_id=ratio-sum expected=5/6 at D12");

            let mut changed = words.clone();
            let final_number = changed.iter_mut().rfind(|word| word.width == 12).unwrap();
            *final_number.bits.last_mut().expect("D12 leaf is nonempty") ^= 1;
            let malformed_pair = zig_transport::encode_t5m_exact_words(&changed).unwrap();
            assert!(eval_verified(&nested, &malformed_pair)
                .unwrap_err()
                .contains("T5M_PAIR_MISMATCH"));
        }

        #[test]
        fn unary_d5_negative_and_reciprocal_execute_via_zig_t5m() {
            // D5 DIFFERENCE (- x) and QUOTIENT (/ x) have existing
            // same-domain unary Core mechanisms. Zig only carries their words.
            for (id, head, input, input_width, expected, expected_width, is_ratio) in [
                ("neg-plus-three", "відняти", 3, 12, "-3", 12, false),
                ("neg-minus-three", "відняти", -3, 12, "3", 12, false),
                ("neg-d24-min", "відняти", -8_388_608, 24, "8388608", 48, false),
                ("reciprocal-three", "частка", 3, 12, "1/3", 12, true),
                ("reciprocal-minus-two", "частка", -2, 12, "-1/2", 12, true),
                ("reciprocal-one", "частка", 1, 12, "1", 12, false),
            ] {
                let source = format!("({head} {input})");
                let admitted = qualify(&source)
                    .unwrap_or_else(|error| panic!("test_id={id} layer=admission {error}"));
                let words = expected_words(&admitted).unwrap();
                assert_eq!(words.len(), 4, "test_id={id} layer=D2 expected=unary-call");
                assert_eq!(
                    words.iter().map(|w| w.width).collect::<Vec<_>>(),
                    vec![2, 5, input_width, 2],
                    "test_id={id} layer=carrier"
                );
                let physical = zig_transport::encode_t5m_exact_words(&words)
                    .expect("Zig encodes unary exact D5/D24 words");
                assert_eq!(
                    zig_transport::decode_t5m_exact_words(&physical).unwrap(),
                    words
                );
                let value = eval_verified(&source, &physical)
                    .unwrap_or_else(|error| panic!("test_id={id} layer=eval {error}"));
                assert_eq!(
                    value.to_string(),
                    expected,
                    "test_id={id} layer=law expected={expected}"
                );
                if is_ratio {
                    assert!(
                        matches!(&value, Value::NumericComposition(_)),
                        "test_id={id} layer=result expected=exact RATIO"
                    );
                } else {
                    let Value::BinaryNumber(ref word) = value else {
                        panic!("test_id={id} layer=result expected=integer Dn");
                    };
                    assert_eq!(word.numeric_domain_width(), Some(expected_width));
                }
            }

            // Чинне українське джерело: лише десяткові значення, без #d24.
            // Одномісні D5:01011 та D5:10111 — справжні виконувані закони.
            for (id, source, expected) in [
                ("decimal-negation", "(відняти 2)", "-2"),
                ("decimal-reciprocal", "(частка 2)", "1/2"),
            ] {
                let words = expected_words(&qualify(source).unwrap()).unwrap();
                assert_eq!(
                    words.iter().map(|w| w.width).collect::<Vec<_>>(),
                    vec![2, 5, 12, 2],
                    "test_id={id} layer=domain"
                );
                let physical = zig_transport::encode_t5m_exact_words(&words).unwrap();
                assert_eq!(
                    zig_transport::decode_t5m_exact_words(&physical).unwrap(),
                    words,
                    "test_id={id} layer=transport"
                );
                assert_eq!(
                    eval_verified(source, &physical).unwrap().to_string(),
                    expected,
                    "test_id={id} layer=SENS"
                );
            }
        }

        #[test]
        fn unary_d5_zero_normalizes_and_zero_reciprocal_fails() {
            let neg_zero = "(відняти 0)".to_string();
            let words = expected_words(&qualify(&neg_zero).unwrap()).unwrap();
            let packed = zig_transport::encode_t5m_exact_words(&words).unwrap();
            let result = eval_verified(&neg_zero, &packed).unwrap();
            let Value::BinaryNumber(ref number) = result else {
                panic!("test_id=negative-zero layer=eval expected=D12 zero");
            };
            assert_eq!(number.numeric_domain_width(), Some(12));
            assert_eq!(number.exact_numeric_domain_bits(), Some(vec![0; 12]));

            let zero_reciprocal = "(частка 0)".to_string();
            let words = expected_words(&qualify(&zero_reciprocal).unwrap()).unwrap();
            let packed = zig_transport::encode_t5m_exact_words(&words).unwrap();
            let error =
                eval_verified(&zero_reciprocal, &packed).expect_err("zero reciprocal is undefined");
            assert!(
                error.starts_with("SENS eval:"),
                "test_id=zero-reciprocal layer=eval actual={error}"
            );
        }

        #[test]
        fn d12_zero_and_number_predicates_execute_after_physical_t5m_roundtrip() {
            // The two source fixtures are authored in SENS/Lisp. The paired
            // source projector explicitly gives their integer leaves D12 identity.
            let cases: [(&str, &str, bool); 7] = [
                ("numberp-zero", "(число? 0)", true),
                ("numberp-negative", "(число? -1)", true),
                (
                    "numberp-ratio",
                    include_str!("../../../../tests/semantic/d5-d12-numberp-law.lisp"),
                    true,
                ),
                ("zerop-zero", "(нуль? 0)", true),
                (
                    "zerop-computed-zero",
                    include_str!("../../../../tests/semantic/d5-d12-zerop-law.lisp"),
                    true,
                ),
                ("zerop-positive", "(нуль? 1)", false),
                ("zerop-negative", "(нуль? -1)", false),
            ];
            for (id, source, expected) in cases {
                let source = source.trim();
                let qualified = qualify(source)
                    .unwrap_or_else(|error| panic!("test_id={id} layer=SENS admission {error}"));
                let words = expected_words(&qualified).unwrap();
                let numeric_widths = words
                    .iter()
                    .filter(|word| word.width > 5)
                    .map(|word| word.width)
                    .collect::<Vec<_>>();
                assert!(
                    !numeric_widths.is_empty() && numeric_widths.iter().all(|&width| width == 12),
                    "test_id={id} layer=D12 expected_only_D12_leaves actual={numeric_widths:?}"
                );
                let physical = zig_transport::encode_t5m_exact_words(&words)
                    .unwrap_or_else(|error| panic!("test_id={id} layer=Zig-T5M encode {error}"));
                assert_eq!(
                    zig_transport::decode_t5m_exact_words(&physical).unwrap(),
                    words,
                    "test_id={id} layer=transport"
                );
                let actual = eval_verified(source, &physical)
                    .unwrap_or_else(|error| panic!("test_id={id} layer=SENS eval {error}"));
                assert_eq!(
                    actual.as_predicate_bit(),
                    Some(expected),
                    "test_id={id} layer=D1 expected={expected}"
                );
            }
        }

        #[test]
        fn unsupported_unary_math_or_wrong_arity_cannot_be_physically_admitted() {
            for source in [
                "(додати 1)".to_string(),
                "(помножити 1)".to_string(),
                "(менше? 1)".to_string(),
                "(більше? 1)".to_string(),
                "(частка 1 2 3)".to_string(),
                "(відняти 1 2 3)".to_string(),
                "(частка)".to_string(),
                "(нуль?)".to_string(),
                "(число?)".to_string(),
                "(нуль? 1 2)".to_string(),
                "(число? 1 2)".to_string(),
            ] {
                assert!(
                    qualify(&source).is_err(),
                    "test_id=arity-admission layer=SENS expected=BLOCK source={source}"
                );
            }
        }

        #[test]
        fn signed_d12_comparisons_return_exact_d1_over_physical_t5m() {
            // D5:11010 LESSP and 11011 GREATERP compare exact D12 operands.
            // The D1 predicate is produced by SENS, not decoded from T5M.
            for (head, left, right, expected) in [
                ("менше?", -1, 1, true),
                ("більше?", 1, -1, true),
                ("менше?", 1, 1, false),
                ("більше?", -1, 1, false),
            ] {
                let source = source(head, left, right);
                let words = expected_words(&qualify(&source).unwrap()).unwrap();
                let physical = zig_transport::encode_t5m_exact_words(&words).unwrap();
                let value = eval_verified(&source, &physical)
                    .unwrap_or_else(|error| panic!("test_id={head} layer=eval actual={error}"));
                assert_eq!(
                    value.as_predicate_bit(),
                    Some(expected),
                    "test_id={head} layer=semantic expected=D1:{expected}"
                );
            }
        }

        #[test]
        fn nested_mixed_domains_must_fail_during_sens_evaluation() {
            // Input leaves themselves are qualified. The inner ADD widens
            // to D48, so outer D24 + D48 has no admitted mixed-domain law.
            let source = format!(
                "(додати {} 1)",
                source("додати", 8_388_607, 1),
            );
            let root = qualify(&source).expect("source words each qualified");
            let words = expected_words(&root).expect("physical structure is valid");
            let physical = zig_transport::encode_t5m_exact_words(&words).unwrap();
            let error = eval_verified(&source, &physical)
                .expect_err("SENS may never silently coerce D48 to D24");
            assert!(
                error.starts_with("SENS eval:"),
                "test_id=nested-mixed-width layer=eval expected=rejection actual={error}"
            );
        }

        #[test]
        fn signed_d24_minimum_widens_to_d48_without_t5m_truncation() {
            // Owner ratification 2026-10-18: signed two's complement.
            // -8_388_608 is a valid D24 atom; subtracting +1 needs D48.
            for (id, input, expected) in [
                ("sub-min", source("відняти", -8_388_608, 1), "-8388609"),
                ("mul-min", source("помножити", -8_388_608, 2), "-16777216"),
                ("sum-negative", source("додати", -8_388_608, -1), "-8388609"),
            ] {
                let admitted = qualify(&input).expect("ratified signed D24 words");
                let words = expected_words(&admitted).expect("exact D5 and D24 structure");
                assert_eq!(words[2].width, 24, "test_id={id} layer=physical width");
                assert_eq!(words[2].bits[0], 1, "test_id={id} layer=physical sign");
                let physical = zig_transport::encode_t5m_exact_words(&words)
                    .expect("Zig must encode all original 24 bits");
                assert_eq!(
                    zig_transport::decode_t5m_exact_words(&physical).unwrap(),
                    words
                );
                let value = eval_verified(&input, &physical)
                    .unwrap_or_else(|error| panic!("test_id={id} layer=SENS eval actual={error}"));
                let Value::BinaryNumber(ref number) = value else {
                    panic!("test_id={id} layer=eval expected=integer D48");
                };
                assert_eq!(
                    number.numeric_domain_width(),
                    Some(48),
                    "test_id={id} layer=domain expected=D48"
                );
                assert_eq!(
                    number.to_decimal_string(),
                    expected,
                    "test_id={id} layer=integer expected={expected}"
                );
                assert_eq!(
                    number.exact_numeric_domain_bits().unwrap().len(),
                    48,
                    "test_id={id} layer=bits expected_width=48"
                );
            }
        }

        #[test]
        fn existing_d48_operands_survive_real_t5m_and_stay_domain_qualified() {
            // The exact D48 word is transported by Zig, never converted to a
            // W8/W9 code, a host integer, or a new D24 identity.
            // Обидва операнди вже D48 за Д24+ числовим законом,
            // без нав'язаного текстом #d48 і без примусової ширини.
            let source = "(помножити -8388609 8388608)";
            let expected = expected_words(&qualify(source).unwrap()).unwrap();
            assert_eq!(
                expected.iter().map(|w| w.width).collect::<Vec<_>>(),
                vec![2, 5, 48, 48, 2]
            );
            let physical = zig_transport::encode_t5m_exact_words(&expected).unwrap();
            assert_eq!(
                zig_transport::decode_t5m_exact_words(&physical).unwrap(),
                expected
            );
            let value = eval_verified(source, &physical).unwrap();
            let Value::BinaryNumber(ref number) = value else {
                panic!("test_id=d48-negative layer=eval expected=integer D48");
            };
            assert_eq!(number.numeric_domain_width(), Some(48));
            assert_eq!(number.to_decimal_string(), "-70368752566272");
            assert_eq!(number.exact_numeric_domain_bits().unwrap().len(), 48);
        }

        #[test]
        fn physical_alias_mutations_in_opcodes_or_widths_are_not_admitted() {
            let original = source("додати", 1, 2);
            let words = expected_words(&qualify(&original).unwrap()).unwrap();
            for (id, mutated) in [
                ("opcode", {
                    let mut words = words.clone();
                    // D5:01010 ADD -> D5:01011 SUB; still valid physical T5M.
                    words[1].bits[4] ^= 1;
                    words
                }),
                ("width", {
                    let mut words = words.clone();
                    // Same payload at a different explicit width is NOT the same Dn.
                    let original_width = words[2].width;
                    words[2] = ExactT5MWord::new(
                        original_width * 2,
                        [vec![0; original_width], words[2].bits.clone()].concat(),
                    ).unwrap();
                    words
                }),
                ("structure", {
                    let mut words = words.clone();
                    words[4].bits = vec![0, 0]; // D2 CLOSE -> SEPARATOR
                    words
                }),
            ] {
                let physical = zig_transport::encode_t5m_exact_words(&mutated)
                    .expect("mutation stays a physically valid T5M carrier");
                let failure = eval_verified(&original, &physical)
                    .expect_err("physical changes must not receive source admission");
                assert!(
                    failure.starts_with("T5M_PAIR_MISMATCH"),
                    "test_id={id} layer=admission expected=pair-mismatch actual={failure}"
                );
            }
        }

        #[test]
        fn d12_t5m_rejects_rational_literals_but_preserves_sens_computed_ratios() {
            // Physical D12/T5M admits integer source operands only. Exact
            // rational values remain valid when produced by SENS's own D5
            // quotient operation and carried as the operation's integer inputs.
            for invalid in [
                "(число? 1/3)",
                "(число? -1/3)",
                "(число? 0,5)",
                "(число? 1e2)",
            ] {
                assert!(
                    qualify(invalid).is_err(),
                    "test_id=d12-rational-literal layer=admission expected=reject source={invalid}"
                );
            }

            let source = "(число? (частка 1 3))";
            let admitted = qualify(source)
                .expect("SENS-computed rational is not a rational source literal");
            let words = expected_words(&admitted).expect("exact D5/D12+ carrier");
            let physical = zig_transport::encode_t5m_exact_words(&words)
                .expect("Zig/T5M carries exact integer operands");
            assert_eq!(
                zig_transport::decode_t5m_exact_words(&physical).unwrap(),
                words,
                "test_id=d12-computed-ratio layer=transport"
            );
            let actual = eval_verified(source, &physical)
                .expect("SENS computes and tests the exact ratio after physical roundtrip");
            assert_eq!(
                actual.as_predicate_bit(),
                Some(true),
                "test_id=d12-computed-ratio layer=SENS expected=D1:так actual={actual}"
            );
        }

        #[test]
        fn physical_t5m_cannot_invent_numeric_admission_or_mutate_exact_bits() {
            for invalid in [
                "(додати 0,5 2)",
                "(додати 1 2 3)",
                "(додати #d24:000000000000000000000001 2)",
                "(додати #b101 2)",
                "(додати #q2:10 2)",
                "(quote #d24:000000000000000000000001)",
            ] {
                assert!(qualify(invalid).is_err(), "unadmitted source={invalid}");
            }
            let admitted = source("додати", 1, 2);
            let words = expected_words(&qualify(&admitted).unwrap()).unwrap();
            let mut altered = words.clone();
            *altered[3].bits.last_mut().expect("numeric leaf is nonempty") ^= 1;
            let alien =
                zig_transport::encode_t5m_exact_words(&altered).expect("valid but wrong T5M data");
            assert!(eval_verified(&admitted, &alien)
                .unwrap_err()
                .contains("T5M_PAIR_MISMATCH"));

            // Exactly equal bare 12-bit payload does NOT carry proof of
            // source identity: without its Lisp companion, this is not runnable.
            let bare = zig_transport::encode_t5m_exact_words(&[words[2].clone()]).unwrap();
            assert!(eval_verified(&admitted, &bare)
                .unwrap_err()
                .contains("T5M_PAIR_MISMATCH"));
        }
    }
}

#[cfg(feature = "zig-transport")]
fn main() {
    paired::main();
}

#[cfg(not(feature = "zig-transport"))]
fn main() {
    eprintln!("RUST_ZIG_ONLY: physical T5M paired execution requires Zig");
    std::process::exit(2);
}
