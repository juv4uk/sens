use sens::{
    installed_capabilities, parse, semantic_registry_export, CoreDomainIdentity, Expr, ExprKind,
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
    blocked_unratified: usize,
    blocked_unratified_heads: HashSet<String>,
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

fn head_kind(identity: CoreDomainIdentity) -> HeadKind {
    // Lisp-owned surface tables decide the *exact* domain and bits.
    // No historical W8, English opcode or bare payload can select a form.
    for (surface, kind) in [
        ("як-є", HeadKind::Quote),
        ("за-умовою", HeadKind::Cond),
        ("функція", HeadKind::Lambda),
        ("визначити", HeadKind::Define),
        ("визначити-макрос", HeadKind::Defmacro),
        ("нехай", HeadKind::Let),
        ("нехай*", HeadKind::LetStar),
    ] {
        if semantic_registry_export::admitted_core_domain_for_surface(surface) == Some(identity) {
            return kind;
        }
    }
    HeadKind::Other
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
) -> Option<(Option<&'a str>, CoreDomainIdentity)> {
    match &head.kind {
        ExprKind::Sid(sens) => Some((None, *sens)),
        ExprKind::Symbol(name) if !bound.contains(name.as_ref()) => {
            if host_capabilities.contains(name.as_ref()) {
                if semantic_registry_export::semantic_id_for_admitted_surface(name).is_some() {
                    analysis.blocked_host_capabilities += 1;
                }
                return None;
            }
            // Audit an unknown, unbound list head as migration debt.
            // Never infer a domain from its spelling or old W8 provenance.
            let admitted = semantic_registry_export::semantic_id_for_admitted_surface(name);
            if admitted.is_none() {
                analysis.blocked_unratified += 1;
                analysis.blocked_unratified_heads.insert(name.to_string());
            }
            admitted.map(|sens| (Some(name.as_ref()), sens))
        }
        _ => None,
    }
}

fn push_head_edit(head: &Expr, spelling: &str, analysis: &mut Analysis) {
    // Historical W8/SID8 is provenance ONLY. A code can be emitted only
    // when the current ratified source-surface index grants its own
    // domain-qualified D3/D4/D5/D6 coordinate.
    let Some(exact) = semantic_registry_export::admitted_core_domain_for_surface(spelling) else {
        return;
    };
    analysis.edits.push(Edit {
        start: head.span.start,
        end: head.span.end,
        replacement: format!("{:0width$b}", exact.packed_bits(), width = exact.width(),),
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
        walk_expr(expression, bound, host_capabilities, analysis, top_level);
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
                walk_sequence(parts, &mut clause_bound, host_capabilities, analysis, false);
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
            // The current Ukrainian spelling is already an exact call
            // in the mixed reader. Other spellings may be migrated only
            // through the ratified domain-qualified source index.
            if semantic_registry_export::exact_uk_callable_for_source_head(spelling).is_none() {
                if semantic_registry_export::admitted_core_domain_for_surface(spelling).is_some() {
                    push_head_edit(head, spelling, analysis);
                } else {
                    // Legacy surface recognition is NOT ratified callable authority.
                    analysis.blocked_unratified += 1;
                }
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
                walk_sequence(&arguments[1..], bound, host_capabilities, analysis, false);
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
                walk_let(arguments, bound, host_capabilities, analysis, false);
                return;
            }
            HeadKind::LetStar => {
                walk_let(arguments, bound, host_capabilities, analysis, true);
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
        walk_expr(head, &mut head_bound, host_capabilities, analysis, false);
    }

    for argument in arguments {
        let mut local = bound.clone();
        walk_expr(argument, &mut local, host_capabilities, analysis, false);
    }
}

/// A table function the language itself defines in Lisp: a code with no
/// Rust primitive and no special form. Its first top-level definition binds
/// the code slot (#1468), so code and name reach the same function.
fn is_language_definition(name: &str) -> bool {
    semantic_registry_export::semantic_id_for_admitted_surface(name).is_some_and(|sens| {
        !matches!(
            semantic_registry_export::function_role(sens),
            Some("primitive") | Some("syntax")
        )
    })
}

fn analyze(source: &str, host_capabilities: &HashSet<String>) -> Result<Analysis, String> {
    analyze_with(source, host_capabilities, false)
}

fn analyze_with(
    source: &str,
    host_capabilities: &HashSet<String>,
    language: bool,
) -> Result<Analysis, String> {
    let expressions = parse(source).map_err(|error| error.render(source))?;
    let mut analysis = Analysis {
        language,
        ..Analysis::default()
    };
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
            println!(
                "Parser-aware repository migration from admitted surfaces to exact SENS functions."
            );
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
            let mut unratified_heads: Vec<_> = analysis.blocked_unratified_heads.iter().collect();
            unratified_heads.sort_unstable();
            println!(
                "{filename}: convertible={} named-calls={} blocked-host={} blocked-unratified={} unratified-heads={}",
                analysis.edits.len(),
                analysis.named_calls,
                analysis.blocked_host_capabilities,
                analysis.blocked_unratified,
                unratified_heads
                    .iter()
                    .map(|name| name.as_str())
                    .collect::<Vec<_>>()
                    .join(",")
            );
            changes_available |= !analysis.edits.is_empty() || analysis.blocked_unratified > 0;
            continue;
        }

        if analysis.blocked_unratified > 0 {
            eprintln!(
                "sens-to-sens: {filename}: BLOCKED_UNRATIFIED_HEADS={} (historical W8 never becomes current domain code)",
                analysis.blocked_unratified
            );
            failed = true;
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
            "{filename}: replaced={} named-calls-remaining={} blocked-host={} blocked-unratified={}",
            analysis.edits.len(),
            remaining.named_calls,
            remaining.blocked_host_capabilities,
            remaining.blocked_unratified
        );
    }

    if failed {
        process::exit(2);
    }
    if check && changes_available {
        process::exit(1);
    }
}

