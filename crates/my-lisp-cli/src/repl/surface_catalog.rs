use my_lisp::syntax::Expr;
use my_lisp::{parse, ExprKind};

const UK_API_DOCS: &str = include_str!("../../../../lib/surface/uk-docs.lisp");
const HUMAN_NAMESPACES: [&str; 3] = ["укр", "en", "sa"];
const FIXED_SURFACES: [&str; 5] = ["en", "ук", "укр", "sa", "sym"];

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

fn registry_entries() -> Result<Vec<SurfaceEntry>, String> {
    let mut entries = Vec::new();

    for semantic_id in my_lisp::semantic_registry_export::admitted_semantic_ids() {
        if semantic_id == 0 {
            continue;
        }

        let admitted =
            my_lisp::semantic_registry_export::admitted_surfaces_for_semantic_id(semantic_id);
        let names = FIXED_SURFACES
            .iter()
            .map(|namespace| {
                let name = admitted
                    .iter()
                    .find(|surface| surface.namespace == *namespace)
                    .map(|surface| surface.name.to_string());
                SurfaceName {
                    surface: (*namespace).to_string(),
                    name,
                }
            })
            .collect();

        entries.push(SurfaceEntry {
            identity: my_lisp::semantic_registry_export::semantic_id_bits(semantic_id),
            names,
        });
    }

    if entries.is_empty() {
        return Err("byte-SID semantic registry contains no surface entries".to_string());
    }
    Ok(entries)
}

fn surface_name<'a>(entry: &'a SurfaceEntry, namespace: &str) -> Option<&'a SurfaceName> {
    entry.names.iter().find(|name| name.surface == namespace)
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
    let ukr = counts_for(&entries, "укр");
    let uk_compat = counts_for(&entries, "ук");
    let en = counts_for(&entries, "en");
    let sa = counts_for(&entries, "sa");
    let symbolic = entries
        .iter()
        .filter(|entry| surface_name(entry, "sym").and_then(|item| item.name.as_deref()).is_some())
        .count();
    let trilingual_present = entries
        .iter()
        .filter(|entry| {
            HUMAN_NAMESPACES.iter().all(|surface| {
                surface_name(entry, surface)
                    .and_then(|name| name.name.as_deref())
                    .is_some()
            })
        })
        .count();

    Ok(format!(
        "Єдина таблиця назв Canon · byte identities: {denominator}\n\
         УКР  present {:>3} · empty {:>3}\n\
         УК   present {:>3} · empty {:>3} · compatibility/compact column\n\
         EN   present {:>3} · empty {:>3}\n\
         SA   present {:>3} · empty {:>3}\n\
         shared sym identities: {symbolic}\n\
         trilingual present (укр/en/sa): {trilingual_present}/{denominator}\n\
         release parity: {}",
        ukr.present,
        ukr.empty,
        uk_compat.present,
        uk_compat.empty,
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

    let counts = counts_for(&entries, surface);
    let mut output = format!(
        "namespace {surface}: present {} · empty {} · total {}\n  ",
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
        "identity: {}\n  УКР: {}\n  УК (compat): {}\n  EN: {}\n  SA: {}",
        entry.identity,
        rendered_name(surface_name(entry, "укр")),
        rendered_name(surface_name(entry, "ук")),
        rendered_name(surface_name(entry, "en")),
        rendered_name(surface_name(entry, "sa")),
    );
    if surface_name(entry, "sym").is_some() {
        output.push_str("\n  SYM: ");
        output.push_str(&rendered_name(surface_name(entry, "sym")));
    }
    output.push_str("\n  current: ");
    output.push_str(surface);

    if surface == "укр" {
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
    fn ukr_is_primary_ukrainian_name_namespace() {
        let entries = registry_entries().expect("numeric registry");
        let entry = find_entry(&entries, "порожній-текст?").expect("ukr identity");
        assert_eq!(entry.identity, "00111100");
        assert_eq!(
            surface_name(entry, "укр").and_then(|item| item.name.as_deref()),
            Some("порожній-текст?")
        );
        assert_eq!(
            surface_name(entry, "ук").and_then(|item| item.name.as_deref()),
            Some("текст-порожній?")
        );
    }

    #[test]
    fn plus_is_shared_symbol_not_english() {
        let entries = registry_entries().expect("numeric registry");
        let entry = find_entry(&entries, "+").expect("+ identity");
        assert_eq!(entry.identity, "00001100");
        assert_eq!(surface_name(entry, "en").and_then(|item| item.name.as_deref()), None);
        assert_eq!(surface_name(entry, "укр").and_then(|item| item.name.as_deref()), Some("додати"));
        assert_eq!(surface_name(entry, "sa").and_then(|item| item.name.as_deref()), Some("yoga"));
        assert_eq!(surface_name(entry, "sym").and_then(|item| item.name.as_deref()), Some("+"));
    }

    #[test]
    fn repl_never_reports_a_human_spelling_as_identity() {
        let output = render_name("укр", "map").expect("render map");
        assert!(output.starts_with("identity: 00110111\n"));
        assert!(!output.contains("identity: map"));
        assert!(output.contains("УКР: відобразити"));

        let plus = render_name("укр", "+").expect("render +");
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
    fn ukr_catalog_is_registry_projection_not_runtime_environment() {
        let output = render_names("укр").expect("ukr catalog");
        assert!(output.starts_with("namespace укр:"));
        assert!(output.contains("порожній-текст?"));
    }

    #[test]
    fn ratified_sanskrit_cond_spelling_is_visible() {
        let output = render_name("sa", "anukrama").expect("cond");
        assert!(output.starts_with("identity: 00000111\n"));
    }
}
