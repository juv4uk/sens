use sens::{parse, semantic_registry_export, Expr, ExprKind, Sens8};
use std::collections::HashSet;
use std::env;
use std::fs;
use std::process;

const QUOTE: u8 = 0b0000_0001;
const ATOM: u8 = 0b0000_0010;
const EQ: u8 = 0b0000_0011;
const CONS: u8 = 0b0000_0100;
const CAR: u8 = 0b0000_0101;
const CDR: u8 = 0b0000_0110;
const COND: u8 = 0b0000_0111;
const LAMBDA: u8 = 0b0000_1000;
const DEFINE: u8 = 0b0000_1001;
const DEFMACRO: u8 = 0b0000_1010;
const DEF_COMPAT: u8 = 0b0000_1011;
const ADD: u8 = 0b0000_1100;
const SUB: u8 = 0b0000_1101;
const MUL: u8 = 0b0000_1110;
const DIV: u8 = 0b0000_1111;
const LT: u8 = 0b0001_1010;
const GT: u8 = 0b0001_1011;
const NUM_EQ: u8 = 0b0001_1100;
const EVAL: u8 = 0b0100_1101;
const AND: u8 = 0b1001_1010;
const OR: u8 = 0b1001_1011;
const LET: u8 = 0b1001_1100;
const LET_STAR: u8 = 0b1001_1101;
const THREAD_FIRST: u8 = 0b1001_1110;
const THREAD_LAST: u8 = 0b1001_1111;

#[derive(Clone, Debug, Eq, PartialEq)]
struct Edit {
    start: usize,
    end: usize,
    replacement: String,
}

#[derive(Default, Debug)]
struct Analysis {
    edits: Vec<Edit>,
    named_calls: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum HeadKind {
    Quote,
    Cond,
    Lambda,
    Define,
    Defmacro,
    Let,
    LetStar,
    RawMacro,
    Primitive,
    Arithmetic,
    Other,
}

fn head_kind(sens: Sens8) -> HeadKind {
    match sens.packed_byte() {
        QUOTE => HeadKind::Quote,
        COND => HeadKind::Cond,
        LAMBDA => HeadKind::Lambda,
        DEFINE | DEF_COMPAT => HeadKind::Define,
        DEFMACRO => HeadKind::Defmacro,
        LET => HeadKind::Let,
        LET_STAR => HeadKind::LetStar,
        AND | OR | THREAD_FIRST | THREAD_LAST => HeadKind::RawMacro,
        ATOM | EQ | CONS | CAR | CDR | LT | GT | NUM_EQ | EVAL => HeadKind::Primitive,
        ADD | SUB | MUL | DIV => HeadKind::Arithmetic,
        _ => HeadKind::Other,
    }
}

fn target_sens(sens: Sens8) -> Sens8 {
    if sens.packed_byte() == DEF_COMPAT {
        Sens8::from_packed_byte(DEFINE)
    } else {
        sens
    }
}

fn resolve_head<'a>(
    head: &'a Expr,
    bound: &HashSet<String>,
) -> Option<(Option<&'a str>, Sens8)> {
    match &head.kind {
        ExprKind::Sid(sens) => Some((None, *sens)),
        ExprKind::Symbol(name) if !bound.contains(name.as_ref()) => {
            semantic_registry_export::semantic_id_for_admitted_surface(name)
                .map(|sens| (Some(name.as_ref()), sens))
        }
        _ => None,
    }
}

fn push_head_edit(head: &Expr, sens: Sens8, analysis: &mut Analysis) {
    analysis.edits.push(Edit {
        start: head.span.start,
        end: head.span.end,
        replacement: format!("{:08b}", target_sens(sens).packed_byte()),
    });
}

fn collect_parameter_names(expression: &Expr, out: &mut HashSet<String>) {
    match &expression.kind {
        ExprKind::Symbol(name) => {
            out.insert(name.to_string());
        }
        ExprKind::List(items) => {
            for item in items.iter() {
                collect_parameter_names(item, out);
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_parameter_names(head, out);
            collect_parameter_names(tail, out);
        }
        _ => {}
    }
}

fn walk_sequence(
    expressions: &[Expr],
    bound: &mut HashSet<String>,
    analysis: &mut Analysis,
) {
    for expression in expressions {
        walk_expr(expression, bound, analysis);
    }
}

fn walk_cond_clauses(arguments: &[Expr], bound: &HashSet<String>, analysis: &mut Analysis) {
    for clause in arguments {
        match &clause.kind {
            ExprKind::List(parts) => {
                let mut clause_bound = bound.clone();
                walk_sequence(parts, &mut clause_bound, analysis);
            }
            _ => {
                let mut local = bound.clone();
                walk_expr(clause, &mut local, analysis);
            }
        }
    }
}

fn walk_let(
    arguments: &[Expr],
    bound: &HashSet<String>,
    analysis: &mut Analysis,
    sequential: bool,
) {
    if arguments.is_empty() {
        return;
    }

    let mut body_bound = bound.clone();
    if let ExprKind::List(bindings) = &arguments[0].kind {
        for binding in bindings.iter() {
            let ExprKind::List(parts) = &binding.kind else {
                continue;
            };
            if parts.is_empty() {
                continue;
            }

            let mut initializer_bound = if sequential {
                body_bound.clone()
            } else {
                bound.clone()
            };
            for value in &parts[1..] {
                walk_expr(value, &mut initializer_bound, analysis);
            }

            if let ExprKind::Symbol(name) = &parts[0].kind {
                body_bound.insert(name.to_string());
            }
        }
    }

    walk_sequence(&arguments[1..], &mut body_bound, analysis);
}

fn walk_expr(
    expression: &Expr,
    bound: &mut HashSet<String>,
    analysis: &mut Analysis,
) {
    let ExprKind::List(items) = &expression.kind else {
        return;
    };
    if items.is_empty() {
        return;
    }

    let head = &items[0];
    let arguments = &items[1..];
    let resolved = resolve_head(head, bound);

    if let Some((surface, sens)) = resolved {
        if surface.is_some() {
            analysis.named_calls += 1;
        }

        let kind = head_kind(sens);
        let replace = surface.is_some()
            && match kind {
                HeadKind::Quote
                | HeadKind::Cond
                | HeadKind::Lambda
                | HeadKind::Define
                | HeadKind::Primitive => true,
                HeadKind::Arithmetic | HeadKind::Other => true,
                HeadKind::Defmacro | HeadKind::Let | HeadKind::LetStar | HeadKind::RawMacro => false,
            };

        if replace {
            push_head_edit(head, sens, analysis);
        }

        match kind {
            HeadKind::Quote => return,
            HeadKind::Lambda => {
                if arguments.is_empty() {
                    return;
                }
                let mut local = bound.clone();
                collect_parameter_names(&arguments[0], &mut local);
                walk_sequence(&arguments[1..], &mut local, analysis);
                return;
            }
            HeadKind::Define => {
                if arguments.is_empty() {
                    return;
                }
                if let ExprKind::Symbol(name) = &arguments[0].kind {
                    bound.insert(name.to_string());
                }
                walk_sequence(&arguments[1..], bound, analysis);
                return;
            }
            HeadKind::Defmacro => {
                if arguments.len() < 2 {
                    return;
                }
                if let ExprKind::Symbol(name) = &arguments[0].kind {
                    bound.insert(name.to_string());
                }
                let mut local = bound.clone();
                collect_parameter_names(&arguments[1], &mut local);
                walk_sequence(&arguments[2..], &mut local, analysis);
                return;
            }
            HeadKind::Let => {
                walk_let(arguments, bound, analysis, false);
                return;
            }
            HeadKind::LetStar => {
                walk_let(arguments, bound, analysis, true);
                return;
            }
            HeadKind::Cond => {
                walk_cond_clauses(arguments, bound, analysis);
                return;
            }
            // Registry-owned macros receive raw syntax. Until their exact-code
            // migration has a dedicated structural witness, do not recurse into
            // those raw forms merely because the macro's surface has a SENS ID.
            HeadKind::RawMacro => return,
            _ => {}
        }
    } else {
        let mut head_bound = bound.clone();
        walk_expr(head, &mut head_bound, analysis);
    }

    for argument in arguments {
        let mut local = bound.clone();
        walk_expr(argument, &mut local, analysis);
    }
}

fn analyze(source: &str) -> Result<Analysis, String> {
    let expressions = parse(source).map_err(|error| error.render(source))?;
    let mut analysis = Analysis::default();
    let mut bound = HashSet::new();
    walk_sequence(&expressions, &mut bound, &mut analysis);
    analysis.edits.sort_by_key(|edit| edit.start);

    for pair in analysis.edits.windows(2) {
        if pair[0].end > pair[1].start {
            return Err("internal error: overlapping source edits".to_string());
        }
    }

    Ok(analysis)
}

fn apply_edits(source: &str, edits: &[Edit]) -> Result<String, String> {
    let mut output = source.to_string();
    for edit in edits.iter().rev() {
        let Some(current) = output.get(edit.start..edit.end) else {
            return Err("internal error: parser span is not a UTF-8 boundary".to_string());
        };
        if current.is_empty() {
            return Err("internal error: empty call-head span".to_string());
        }
        output.replace_range(edit.start..edit.end, &edit.replacement);
    }
    Ok(output)
}

fn usage() {
    eprintln!("Usage: sens-to-sens [--check] <file>...");
}

fn main() {
    let mut check = false;
    let mut files = Vec::new();

    for argument in env::args().skip(1) {
        if argument == "--check" {
            check = true;
        } else if argument == "-h" || argument == "--help" {
            println!("Usage: sens-to-sens [--check] <file>...");
            println!("Rewrites only parser-proven call heads that currently have a safe SENS mechanism.");
            println!("--check reports candidates without writing and exits 1 when changes are available.");
            return;
        } else if argument.starts_with('-') {
            eprintln!("sens-to-sens: unknown option: {argument}");
            usage();
            process::exit(2);
        } else {
            files.push(argument);
        }
    }

    if files.is_empty() {
        usage();
        process::exit(2);
    }

    let mut failed = false;
    let mut changes_available = false;

    for filename in files {
        let source = match fs::read_to_string(&filename) {
            Ok(source) => source,
            Err(error) => {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        };

        let analysis = match analyze(&source) {
            Ok(analysis) => analysis,
            Err(error) => {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        };

        if check {
            println!(
                "{filename}: convertible={} named-calls={}",
                analysis.edits.len(),
                analysis.named_calls
            );
            changes_available |= !analysis.edits.is_empty();
            continue;
        }

        let output = match apply_edits(&source, &analysis.edits) {
            Ok(output) => output,
            Err(error) => {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        };

        if let Err(error) = analyze(&output) {
            eprintln!("sens-to-sens: {filename}: rewritten source does not parse: {error}");
            failed = true;
            continue;
        }

        if output != source {
            if let Err(error) = fs::write(&filename, &output) {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        }

        let remaining = analyze(&output).expect("rewritten source was just validated");
        println!(
            "{filename}: replaced={} named-calls-remaining={}",
            analysis.edits.len(),
            remaining.named_calls
        );
    }

    if failed {
        process::exit(2);
    }
    if check && changes_available {
        process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rewrite(source: &str) -> String {
        let analysis = analyze(source).expect("source parses");
        apply_edits(source, &analysis.edits).expect("edits apply")
    }

    #[test]
    fn preserves_comments_strings_and_quote_data() {
        let source = "; (+ 8 9)\n(quote (+ 1 2))\n\"car (+ 3 4)\"\n(atom? x)\n";
        let expected =
            "; (+ 8 9)\n(00000001 (+ 1 2))\n\"car (+ 3 4)\"\n(00000010 x)\n";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn current_primitives_rewrite_at_runtime_arity_and_respect_lambda_shadowing() {
        let source = "(+ 1 2) (+ 1 2 3) (< 1 2 3) (eval x) (lambda (+) (+ 4 5))";
        let expected = "(00001100 1 2) (00001100 1 2 3) (00011010 1 2 3) (01001101 x) (00001000 (+) (+ 4 5))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn define_target_is_data_and_def_compat_migrates_to_define_code() {
        let source = "(def f (lambda (x) (car x))) (define + (lambda (a b) a)) (+ 1 2)";
        let expected =
            "(00001001 f (00001000 (x) (00000101 x))) (00001001 + (00001000 (a b) a)) (+ 1 2)";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn top_level_registry_redefinition_shadows_the_surface_but_not_exact_sens() {
        let source =
            "(define + (lambda (a b) a)) (+ 1 2) (00001100 1 2)";
        let expected =
            "(00001001 + (00001000 (a b) a)) (+ 1 2) (00001100 1 2)";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn unshadowed_language_defined_registry_calls_rewrite_after_1455() {
        let source = "(list 1 2) (member? 2 (quote (1 2 3))) (quotient 17 5) (append (quote (1)) (quote (2)))";
        let expected = "(00100111 1 2) (00101100 2 (00000001 (1 2 3))) (00010100 17 5) (00101001 (00000001 (1)) (00000001 (2)))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn raw_macro_heads_remain_gated_without_rewriting_their_argument_syntax() {
        let source = "(and (+ 1 2) (member? 2 (quote (1 2)))) (or (car x) y) (-> x (car))";
        assert_eq!(rewrite(source), source);
    }

    #[test]
    fn direct_sens_quote_also_protects_quoted_data() {
        assert_eq!(rewrite("(00000001 (car (+ 1 2)))"), "(00000001 (car (+ 1 2)))");
    }

    #[test]
    fn let_binding_positions_are_not_mistaken_for_calls() {
        let source =
            "(let ((car (lambda (x) x)) (y (+ 1 2))) (car (+ y 4)))";
        let expected =
            "(let ((car (00001000 (x) x)) (y (00001100 1 2))) (car (00001100 y 4)))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn let_star_initializer_sees_prior_shadowing() {
        let source =
            "(let* ((+ (lambda (a b) a)) (y (+ 1 2))) y)";
        let expected =
            "(let* ((+ (00001000 (a b) a)) (y (+ 1 2))) y)";
        assert_eq!(rewrite(source), expected);
    }
}
