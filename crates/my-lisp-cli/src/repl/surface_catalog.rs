use my_lisp::syntax::Expr;
use my_lisp::{parse, ExprKind};

const REGISTRY: &str = include_str!("../../../../lib/surface/semantic-registry.lisp");
const UK_API_DOCS: &str = include_str!("../../../../lib/surface/uk-docs.lisp");
const HUMAN_SURFACES: [&str; 3] = ["uk", "en", "sa"];

#[derive(Clone, Debug, Eq, PartialEq)]
struct SurfaceName {
    surface: String,
    name: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct SurfaceEntry {
    identity: String,
    names: Vec<SurfaceName>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct SurfaceDoc {
    category: String,
    identity: String,
    kind: String,
    call: String,
    description: String,
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
struct Counts {
    present: usize,
    empty: usize,
}

impl Counts {
    fn add(&mut self, present: bool) {
        if present {
            self.present += 1;
        } else {
            self.empty += 1;
        }
    }
}

fn normalize_surface(surface: &str) -> &str {
    match surface {
        "ук" => "uk",
        other => other,
    }
}

fn surface_groups(line: &str) -> Vec<&str> {
    let mut groups = Vec::new();
    let mut depth = 0usize;
    let mut start = None;

    for (index, byte) in line.bytes().enumerate() {
        match byte {
            b'(' => {
                depth += 1;
                if depth == 2 {
                    start = Some(index + 1);
                }
            }
            b')' => {
                if depth == 2 {
                    if let Some(group_start) = start.take() {
                        let group = line[group_start..index].trim();
                        if !group.is_empty() {
                            groups.push(group);
                        }
                    }
                }
                depth = depth.saturating_sub(1);
            }
            _ => {}
        }
    }
    groups
}

fn registry_name_token(token: &str) -> &str {
    token
        .strip_prefix('"')
        .and_then(|value| value.strip_suffix('"'))
        .unwrap_or(token)
}

fn registry_entries() -> Result<Vec<SurfaceEntry>, String> {
    let mut entries = Vec::new();
    const FIXED_SURFACES: [&str; 5] = ["en", "uk", "ukr", "sa", "sym"];

    for (index, line) in REGISTRY.lines().enumerate() {
        let fields = line.split_whitespace().collect::<Vec<_>>();
        let Some(first) = fields.first() else {
            continue;
        };
        if !first.starts_with('(') {
            continue;
        }
        let Some(identity) = first
            .strip_prefix("(\"")
            .and_then(|value| value.strip_suffix('\"'))
        else {
            continue;
        };
        if identity.len() != 8
            || !identity.bytes().all(|byte| matches!(byte, b'0' | b'1'))
        {
            return Err(format!("registry line {}: invalid byte SID", index + 1));
        }
        if identity == "00000000" {
            continue;
        }

        let mut names = Vec::new();
        for group in surface_groups(line) {
            let fields = group.split_whitespace().collect::<Vec<_>>();
            let (surface, name) = match fields.as_slice() {
                [surface, "()"] => ((*surface).to_string(), None),
                [surface, raw_name] => (
                    (*surface).to_string(),
                    Some(registry_name_token(raw_name).to_string()),
                ),
                _ => {
                    return Err(format!(
                        "registry line {}: malformed status-free sr/2 surface ({group})",
                        index + 1
                    ));
                }
            };

            if names.iter().any(|item: &SurfaceName| item.surface == surface) {
                return Err(format!(
                    "registry line {}: duplicate surface {surface}",
                    index + 1
                ));
            }
            names.push(SurfaceName { surface, name });
        }

        let actual = names
            .iter()
            .map(|item| item.surface.as_str())
            .collect::<Vec<_>>();
        if actual != FIXED_SURFACES {
            return Err(format!(
                "registry line {}: {identity} must contain fixed en/uk/ukr/sa/sym slots",
                index + 1
            ));
        }

        entries.push(SurfaceEntry {
            identity: identity.to_string(),
            names,
        });
    }

    if entries.is_empty() {
        return Err("byte-SID semantic registry contains no surface entries".to_string());
    }
    Ok(entries)
}

fn surface_name<'a>(entry: &'a SurfaceEntry, surface: &str) -> Option<&'a SurfaceName> {
    let surface = normalize_surface(surface);
    entry.names.iter().find(|name| name.surface == surface)
}

fn counts_for(entries: &[SurfaceEntry], surface: &str) -> Counts {
    let mut counts = Counts::default();
    for entry in entries {
        let present = surface_name(entry, surface)
            .and_then(|name| name.name.as_deref())
            .is_some();
        counts.add(present);
    }
    counts
}

fn public_denominator(entries: &[SurfaceEntry]) -> usize {
    entries.len()
}

fn find_entry<'a>(entries: &'a [SurfaceEntry], requested: &str) -> Option<&'a SurfaceEntry> {
    entries.iter().find(|entry| {
        entry.identity == requested
            || entry
                .names
                .iter()
                .any(|surface| surface.name.as_deref() == Some(requested))
    })
}

fn rendered_name(surface: Option<&SurfaceName>) -> String {
    surface
        .and_then(|surface| surface.name.as_deref())
        .unwrap_or("()")
        .to_string()
}

fn expr_list(expr: &Expr) -> Option<&[Expr]> {
    match &expr.kind {
        ExprKind::List(items) => Some(items.as_ref()),
        _ => None,
    }
}

fn expr_symbol(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::Symbol(symbol) => Some(symbol.as_ref()),
        _ => None,
    }
}

fn expr_string(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::String(text) => Some(text.as_ref()),
        _ => None,
    }
}

fn expr_byte_sid(expr: &Expr) -> Option<&str> {
    let bits = expr_string(expr)?;
    (bits.len() == 8 && bits.bytes().all(|byte| matches!(byte, b'0' | b'1')))
        .then_some(bits)
}

fn ukrainian_docs() -> Result<Vec<SurfaceDoc>, String> {
    let program = parse(UK_API_DOCS)
        .map_err(|error| format!("не вдалося прочитати uk-docs.wsm: {}", error.render(UK_API_DOCS)))?;
    let root = program
        .first()
        .and_then(expr_list)
        .ok_or_else(|| "uk-docs.wsm: очікувався кореневий список".to_string())?;
    if root.first().and_then(expr_symbol) != Some("uk-api-docs") {
        return Err("uk-docs.wsm: невідомий кореневий тег".to_string());
    }
    let docs_form = root
        .iter()
        .filter_map(expr_list)
        .find(|items| items.first().and_then(expr_symbol) == Some("docs"))
        .ok_or_else(|| "uk-docs.wsm: відсутня секція docs".to_string())?;

    docs_form
        .iter()
        .skip(1)
        .map(|entry| {
            let fields =
                expr_list(entry).ok_or_else(|| "uk-docs.wsm: doc має бути списком".to_string())?;
            if fields.len() != 6 || fields.first().and_then(expr_symbol) != Some("doc") {
                return Err("uk-docs.wsm: некоректний doc-запис".to_string());
            }
            Ok(SurfaceDoc {
                category: expr_symbol(&fields[1])
                    .ok_or_else(|| "uk-docs.wsm: category має бути символом".to_string())?
                    .to_string(),
                identity: expr_byte_sid(&fields[2])
                    .ok_or_else(|| "uk-docs.wsm: byte SID має бути 8-бітним рядком".to_string())?
                    .to_string(),
                kind: expr_symbol(&fields[3])
                    .ok_or_else(|| "uk-docs.wsm: kind має бути символом".to_string())?
                    .to_string(),
                call: expr_string(&fields[4])
                    .ok_or_else(|| "uk-docs.wsm: call має бути рядком".to_string())?
                    .to_string(),
                description: expr_string(&fields[5])
                    .ok_or_else(|| "uk-docs.wsm: description має бути рядком".to_string())?
                    .to_string(),
            })
        })
        .collect()
}

pub(crate) fn render_status() -> Result<String, String> {
    let entries = registry_entries()?;
    let denominator = public_denominator(&entries);
    let uk = counts_for(&entries, "uk");
    let en = counts_for(&entries, "en");
    let sa = counts_for(&entries, "sa");
    let symbolic = entries
        .iter()
        .filter(|entry| surface_name(entry, "sym").and_then(|item| item.name.as_deref()).is_some())
        .count();
    let trilingual_present = entries
        .iter()
        .filter(|entry| {
            HUMAN_SURFACES.iter().all(|surface| {
                surface_name(entry, surface)
                    .and_then(|name| name.name.as_deref())
                    .is_some()
            })
        })
        .count();

    Ok(format!(
        "Рівноправні людські поверхні · byte identities: {denominator}\n\
         UK  present {:>3} · empty {:>3}\n\
         EN  present {:>3} · empty {:>3}\n\
         SA  present {:>3} · empty {:>3}\n\
         shared sym identities: {symbolic}\n\
         trilingual present: {trilingual_present}/{denominator}\n\
         release parity: {}",
        uk.present,
        uk.empty,
        en.present,
        en.empty,
        sa.present,
        sa.empty,
        if trilingual_present == denominator {
            "CONFIRMED"
        } else {
            "OPEN"
        }
    ))
}

pub(crate) fn render_names(surface: &str) -> Result<String, String> {
    let entries = registry_entries()?;
    if surface == "core" {
        let mut output = format!(
            "core: byte semantic identities · {}\n",
            public_denominator(&entries)
        );
        for (index, entry) in entries.iter().enumerate() {
            if index > 0 {
                output.push_str(if index % 12 == 0 { "\n" } else { " · " });
            }
            output.push_str(&entry.identity);
        }
        output.push_str("\n\ncore показує machine handles; людські назви дивіться через :ім'я <ID>.");
        return Ok(output);
    }

    let surface = normalize_surface(surface);
    let counts = counts_for(&entries, surface);
    let mut output = format!(
        "surface {surface}: present {} · empty {} · total {}\n  ",
        counts.present,
        counts.empty,
        entries.len()
    );
    let mut first = true;
    for entry in &entries {
        let Some(slot) = surface_name(entry, surface) else {
            continue;
        };
        if !first {
            output.push_str(" · ");
        }
        first = false;
        match slot.name.as_deref() {
            Some(name) => output.push_str(name),
            None => {
                output.push_str("(){");
                output.push_str(&entry.identity);
                output.push('}');
            }
        }
    }
    Ok(output)
}

pub(crate) fn render_name(surface: &str, requested: &str) -> Result<String, String> {
    let entries = registry_entries()?;
    let Some(entry) = find_entry(&entries, requested) else {
        return Ok(format!(
            "«{requested}» не знайдено у byte-SID semantic registry; сире середовище перевіряється через (env)/(середовище)."
        ));
    };

    let mut output = format!(
        "identity: {}\n  UK: {}\n  EN: {}\n  SA: {}",
        entry.identity,
        rendered_name(surface_name(entry, "uk")),
        rendered_name(surface_name(entry, "en")),
        rendered_name(surface_name(entry, "sa")),
    );
    if surface_name(entry, "sym").is_some() {
        output.push_str("\n  SYM: ");
        output.push_str(&rendered_name(surface_name(entry, "sym")));
    }
    output.push_str("\n  current: ");
    output.push_str(surface);

    if normalize_surface(surface) == "uk" {
        if let Some(doc) = ukrainian_docs()?
            .into_iter()
            .find(|doc| doc.identity == entry.identity)
        {
            output.push_str("\n  категорія: ");
            output.push_str(&doc.category);
            output.push_str("\n  тип: ");
            output.push_str(&doc.kind);
            output.push_str("\n  виклик: ");
            output.push_str(&doc.call);
            output.push_str("\n  ");
            output.push_str(&doc.description);
        }
    }
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn byte_sid_is_the_only_machine_key() {
        let entries = registry_entries().expect("byte registry");
        for requested in ["00110111", "map", "відобразити", "āvartana"] {
            assert_eq!(
                find_entry(&entries, requested).map(|entry| entry.identity.as_str()),
                Some("00110111")
            );
        }
    }

    #[test]
    fn plus_is_shared_symbol_not_english() {
        let entries = registry_entries().expect("numeric registry");
        let entry = find_entry(&entries, "+").expect("+ identity");
        assert_eq!(entry.identity, "00001100");
        assert_eq!(surface_name(entry, "en").and_then(|item| item.name.as_deref()), None);
        assert_eq!(surface_name(entry, "uk").and_then(|item| item.name.as_deref()), Some("додати"));
        assert_eq!(surface_name(entry, "sa").and_then(|item| item.name.as_deref()), Some("yoga"));
        assert_eq!(surface_name(entry, "sym").and_then(|item| item.name.as_deref()), Some("+"));
    }

    #[test]
    fn repl_never_reports_a_human_spelling_as_identity() {
        let output = render_name("uk", "map").expect("render map");
        assert!(output.starts_with("identity: 00110111\n"));
        assert!(!output.contains("identity: map"));

        let plus = render_name("uk", "+").expect("render +");
        assert!(plus.starts_with("identity: 00001100\n"));
        assert!(plus.contains("EN: ()"));
        assert!(plus.contains("SYM: +"));
    }

    #[test]
    fn core_catalog_is_byte_sid() {
        let output = render_names("core").expect("core catalog");
        assert!(output.contains("00110111"));
        assert!(output.contains("00001100"));
        assert!(!output.contains(" · map"));
    }

    #[test]
    fn ratified_sanskrit_cond_spelling_is_visible() {
        let output = render_name("sa", "anukrama").expect("cond");
        assert!(output.starts_with("identity: 00000111\n"));
    }
}
