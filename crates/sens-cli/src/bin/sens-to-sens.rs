use sens::{
    installed_capabilities, parse, semantic_registry_export, Expr, ExprKind, Sens8,
};
use std::collections::HashSet;
use std::env;
use std::fs;
use std::process;

#[derive(Clone, Debug, Eq, PartialEq)]
struct Edit {
    start: usize,
    end: usize,
    replacement: String,
}

#[derive(Default, Debug)]
struct Analysis {
    /// `--language`: this file defines the language's own table functions.
    language: bool,
    edits: Vec<Edit>,
    named_calls: usize,
    blocked_host_capabilities: usize,
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
    Other,
}

fn head_kind(sens: Sens8) -> HeadKind {
    if sens == sens::sens!(00000001) {
        HeadKind::Quote
    } else if sens == sens::sens!(00000111) {
        HeadKind::Cond
    } else if sens == sens::sens!(00001000) {
        HeadKind::Lambda
    } else if sens == sens::sens!(00001001) || sens == sens::sens!(00001011) {
        HeadKind::Define
    } else if sens == sens::sens!(00001010) {
        HeadKind::Defmacro
    } else if sens == sens::sens!(10011100) {
        HeadKind::Let
    } else if sens == sens::sens!(10011101) {
        HeadKind::LetStar
    } else {
        HeadKind::Other
    }
}

fn target_sens(sens: Sens8) -> Sens8 {
    if sens == sens::sens!(00001011) {
        sens::sens!(00001001)
    } else {
        sens
    }
}

fn host_capability_names() -> HashSet<String> {
    sens_host::install();
    installed_capabilities().into_iter().collect()
}

fn resolve_head<'a>(
    head: &'a Expr,
    bound: &HashSet<String>,
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
) -> Option<(Option<&'a str>, Sens8)> {
    match &head.kind {
        ExprKind::Sid(sens) => Some((None, *sens)),
        ExprKind::Symbol(name) if !bound.contains(name.as_ref()) => {
            if host_capabilities.contains(name.as_ref()) {
                if semantic_registry_export::semantic_id_for_admitted_surface(name).is_some() {
                    analysis.blocked_host_capabilities += 1;
                }
                return None;
            }
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
        replacement: target_sens(sens).to_string(),
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
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
    top_level: bool,
) {
    for expression in expressions {
        walk_expr(
            expression,
            bound,
            host_capabilities,
            analysis,
            top_level,
        );
    }
}

fn walk_cond_clauses(
    arguments: &[Expr],
    bound: &HashSet<String>,
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
) {
    for clause in arguments {
        match &clause.kind {
            ExprKind::List(parts) => {
                let mut clause_bound = bound.clone();
                walk_sequence(
                    parts,
                    &mut clause_bound,
                    host_capabilities,
                    analysis,
                    false,
                );
            }
            _ => {
                let mut local = bound.clone();
                walk_expr(clause, &mut local, host_capabilities, analysis, false);
            }
        }
    }
}

fn walk_let(
    arguments: &[Expr],
    bound: &HashSet<String>,
    host_capabilities: &HashSet<String>,
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
                walk_expr(
                    value,
                    &mut initializer_bound,
                    host_capabilities,
                    analysis,
                    false,
                );
            }

            if let ExprKind::Symbol(name) = &parts[0].kind {
                body_bound.insert(name.to_string());
            }
        }
    }

    walk_sequence(
        &arguments[1..],
        &mut body_bound,
        host_capabilities,
        analysis,
        false,
    );
}

fn walk_expr(
    expression: &Expr,
    bound: &mut HashSet<String>,
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
    top_level: bool,
) {
    let ExprKind::List(items) = &expression.kind else {
        return;
    };
    if items.is_empty() {
        return;
    }

    let head = &items[0];
    let arguments = &items[1..];
    let resolved = resolve_head(head, bound, host_capabilities, analysis);

    if let Some((surface, sens)) = resolved {
        if surface.is_some() {
            analysis.named_calls += 1;
        }

        let kind = head_kind(sens);
        if let Some(spelling) = surface {
            // Current owner-ratified Ukrainian .lisp source heads ALREADY
            // lower to exact-width DomainIdentity in the mixed reader.
            // The historical Sens8 compatibility registry must not convert
            // that primary source back to old 8-bit tokens. Keep counting
            // the call as observed; only the legacy rewrite is suppressed.
            if sens::semantic_registry_export::exact_uk_callable_for_source_head(spelling)
                .is_none()
            {
                push_head_edit(head, sens, analysis);
            }
        }

        match kind {
            HeadKind::Quote => return,
            HeadKind::Lambda => {
                if arguments.is_empty() {
                    return;
                }
                let mut local = bound.clone();
                collect_parameter_names(&arguments[0], &mut local);
                walk_sequence(
                    &arguments[1..],
                    &mut local,
                    host_capabilities,
                    analysis,
                    false,
                );
                return;
            }
            HeadKind::Define => {
                if arguments.is_empty() {
                    return;
                }
                if let ExprKind::Symbol(name) = &arguments[0].kind {
                    // Generic source migration must preserve lexical/surface
                    // shadowing. #1468 pins exact code slots to the first
                    // language definition, so a later top-level surface
                    // redefinition must NOT be rewritten to that old slot.
                    // With `--language` the file *is* that first definition:
                    // its calls reach the same function through the code.
                    if !(analysis.language && top_level && is_language_definition(name)) {
                        bound.insert(name.to_string());
                    }
                }
                walk_sequence(
                    &arguments[1..],
                    bound,
                    host_capabilities,
                    analysis,
                    false,
                );
                return;
            }
            HeadKind::Defmacro => {
                if arguments.len() < 2 {
                    return;
                }
                if let ExprKind::Symbol(name) = &arguments[0].kind {
                    // A macro definition shadows the human surface just like an
                    // ordinary definition. Exact SENS remains pinned to its
                    // existing function slot, so later calls through this
                    // spelling must stay textual.
                    bound.insert(name.to_string());
                }
                let mut local = bound.clone();
                collect_parameter_names(&arguments[1], &mut local);
                walk_sequence(
                    &arguments[2..],
                    &mut local,
                    host_capabilities,
                    analysis,
                    false,
                );
                return;
            }
            HeadKind::Let => {
                walk_let(
                    arguments,
                    bound,
                    host_capabilities,
                    analysis,
                    false,
                );
                return;
            }
            HeadKind::LetStar => {
                walk_let(
                    arguments,
                    bound,
                    host_capabilities,
                    analysis,
                    true,
                );
                return;
            }
            HeadKind::Cond => {
                walk_cond_clauses(arguments, bound, host_capabilities, analysis);
                return;
            }
            HeadKind::Other => {}
        }
    } else {
        let mut head_bound = bound.clone();
        walk_expr(
            head,
            &mut head_bound,
            host_capabilities,
            analysis,
            false,
        );
    }

    for argument in arguments {
        let mut local = bound.clone();
        walk_expr(
            argument,
            &mut local,
            host_capabilities,
            analysis,
            false,
        );
    }
}

/// A table function the language itself defines in Lisp: a code with no
/// Rust primitive and no special form. Its first top-level definition binds
/// the code slot (#1468), so code and name reach the same function.
fn is_language_definition(name: &str) -> bool {
    semantic_registry_export::semantic_id_for_admitted_surface(name)
        .is_some_and(|sens| {
            !matches!(
                semantic_registry_export::function_role(sens),
                Some("primitive") | Some("syntax")
            )
        })
}

fn analyze(
    source: &str,
    host_capabilities: &HashSet<String>,
) -> Result<Analysis, String> {
    analyze_with(source, host_capabilities, false)
}

fn analyze_with(
    source: &str,
    host_capabilities: &HashSet<String>,
    language: bool,
) -> Result<Analysis, String> {
    let expressions = parse(source).map_err(|error| error.render(source))?;
    let mut analysis = Analysis { language, ..Analysis::default() };
    let mut bound = HashSet::new();
    walk_sequence(
        &expressions,
        &mut bound,
        host_capabilities,
        &mut analysis,
        true,
    );
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
    eprintln!("Usage: sens-to-sens [--check] [--language] <file>...");
}

fn main() {
    let mut check = false;
    let mut language = false;
    let mut files = Vec::new();

    for argument in env::args().skip(1) {
        if argument == "--check" {
            check = true;
        } else if argument == "--language" {
            language = true;
        } else if argument == "-h" || argument == "--help" {
            println!("Usage: sens-to-sens [--check] [--language] <file>...");
            println!("Parser-aware repository migration from admitted surfaces to exact SENS functions.");
            println!("--check reports candidates without writing and exits 1 when changes are available.");
            println!("--language: the files are the language's own first definitions of table");
            println!("  functions (code slots, #1468); calls to them become codes too.");
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

    let host_capabilities = host_capability_names();
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

        let analysis = match analyze_with(&source, &host_capabilities, language) {
            Ok(analysis) => analysis,
            Err(error) => {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        };

        if check {
            println!(
                "{filename}: convertible={} named-calls={} blocked-host={}",
                analysis.edits.len(),
                analysis.named_calls,
                analysis.blocked_host_capabilities
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

        if let Err(error) = analyze(&output, &host_capabilities) {
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

        let remaining =
            analyze(&output, &host_capabilities).expect("rewritten source was just validated");
        println!(
            "{filename}: replaced={} named-calls-remaining={} blocked-host={}",
            analysis.edits.len(),
            remaining.named_calls,
            remaining.blocked_host_capabilities
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

    fn no_host() -> HashSet<String> {
        HashSet::new()
    }

    fn rewrite(source: &str) -> String {
        let hosts = no_host();
        let analysis = analyze(source, &hosts).expect("source parses");
        apply_edits(source, &analysis.edits).expect("edits apply")
    }

    #[test]
    fn ratified_uk_source_heads_remain_primary_not_old_eight_bit_tokens() {
        // Source/UI .lisp must stay Ukrainian, while its executable heads
        // lower to exact D3/D4 identities. Do not regress them into SID8.
        let source = "(визначити звязок (функція (x) (сполучити (перше x) (решта x))))\\n";
        let source = source.replace("\\n", "\n");
        let host = no_host();
        let inspected = analyze(&source, &host).expect("canonical Ukrainian source");
        assert!(inspected.named_calls >= 5, "the legacy auditor still sees the calls");
        assert_eq!(inspected.edits.len(), 0, "no Ukrainian exact head can be rewritten to SID8");
        assert_eq!(rewrite(&source), source);

        let mixed = sens::parse_mixed_exact_domain(&source).expect("current exact reader");
        let ExprKind::List(forms) = &mixed[0].kind else {
            panic!("canonical DEFINE must remain a list");
        };
        assert!(matches!(&forms[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 4 && id.packed_bits() == 0b0011));
    }

    #[test]
    fn preserves_comments_strings_and_quote_data() {
        let source = "; (+ 8 9)\n(quote (+ 1 2))\n\"car (+ 3 4)\"\n(atom? x)\n";
        let expected =
            "; (+ 8 9)\n(00000001 (+ 1 2))\n\"car (+ 3 4)\"\n(00000010 x)\n";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn derived_functions_and_current_macros_use_exact_codes() {
        let source =
            "(let ((xs (list 1 2 3))) (and (member? 2 xs) (or () (length xs))))";
        let expected =
            "(10011100 ((xs (00100111 1 2 3))) (10011010 (00101100 2 xs) (10011011 () (00101000 xs))))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn defmacro_head_is_exact_and_its_target_shadows_later_surface_calls() {
        let source =
            "(defmacro list (x) (quote shadowed)) (list (never-defined-function))";
        let expected =
            "(00001010 list (x) (00000001 shadowed)) (list (never-defined-function))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn local_bindings_shadow_registry_surfaces() {
        let source =
            "(lambda (list) (list 1 2)) (let ((car (lambda (x) x))) (car (list 1 2)))";
        let expected =
            "(00001000 (list) (list 1 2)) (10011100 ((car (00001000 (x) x))) (car (00100111 1 2)))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn top_level_and_local_definitions_shadow_registry_surfaces() {
        let source =
            "(define list (lambda args (quote shadowed))) (list 1 2) (lambda () (define list (lambda args 7)) (list 1 2))";
        let expected =
            "(00001001 list (00001000 args (00000001 shadowed))) (list 1 2) (00001000 () (00001001 list (00001000 args 7)) (list 1 2))";
        assert_eq!(rewrite(source), expected);
    }

    fn rewrite_language(source: &str) -> String {
        let analysis = analyze_with(source, &HashSet::new(), true).expect("source analyzes");
        apply_edits(source, &analysis.edits).expect("edits apply")
    }

    #[test]
    fn language_definition_of_library_function_does_not_shadow_its_code() {
        // `reverse` has no primitive: the language's first definition binds
        // code slot 00101010 (#1468), so calls to it become the code.
        assert_eq!(
            rewrite_language("(define reverse (lambda (xs) (reverse xs))) (reverse (list 1))"),
            "(00001001 reverse (00001000 (xs) (00101010 xs))) (00101010 (00100111 1))"
        );
        // A primitive surface still shadows: redefining it is not the language's function.
        assert_eq!(
            rewrite_language("(define car (lambda (x) x)) (car 1)"),
            "(00001001 car (00001000 (x) x)) (car 1)"
        );
        // Local definitions always shadow.
        assert_eq!(
            rewrite_language("(lambda () (define reverse (lambda (x) x)) (reverse 1))"),
            "(00001000 () (00001001 reverse (00001000 (x) x)) (reverse 1))"
        );
    }

    #[test]
    fn compatibility_def_maps_to_define_code() {
        assert_eq!(
            rewrite("(def f (lambda (x) (car x)))"),
            "(00001001 f (00001000 (x) (00000101 x)))"
        );
    }

    #[test]
    fn direct_sens_quote_protects_quoted_data() {
        assert_eq!(
            rewrite("(00000001 (car (list 1 2)))"),
            "(00000001 (car (list 1 2)))"
        );
    }

    #[test]
    fn host_capability_collision_is_never_rewritten() {
        let source = "(car x)";
        let mut hosts = HashSet::new();
        hosts.insert("car".to_string());
        let analysis = analyze(source, &hosts).expect("source parses");
        assert!(analysis.edits.is_empty());
        assert_eq!(analysis.blocked_host_capabilities, 1);
    }

    #[test]
    fn public_sens_display_is_the_replacement_format() {
        assert_eq!(target_sens(sens::sens!(00000101)).to_string(), "00000101");
        assert_eq!(target_sens(sens::sens!(00001011)).to_string(), "00001001");
    }
}
