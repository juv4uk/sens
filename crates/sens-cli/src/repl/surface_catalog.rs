use sens::syntax::Expr;
use sens::{parse, ExprKind};
use std::collections::HashMap;
use std::sync::OnceLock;

const HUMAN_SURFACES: [&str; 4] = ["ук", "укр", "en", "san"];
const FIXED_SURFACES: [&str; 6] = ["ук", "укр", "san", "en", "LISP", "sym"];

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

#[cfg(test)]
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
        "sa" => "san",
        _ => surface,
    }
}

// The REPL is the human-projection exception: Rust reads these Lisp tables
// only to render/resolve UI names; they do not enter the binary backend.
// A table is an immutable, build-embedded projection. Parsing all eleven
// tables on every invoked head makes large executable .lisp programs needlessly slow.
static SURFACE_ENTRIES: OnceLock<Result<Vec<SurfaceEntry>, String>> = OnceLock::new();

fn registry_entries() -> Result<&'static [SurfaceEntry], String> {
    SURFACE_ENTRIES
        .get_or_init(load_registry_entries)
        .as_ref()
        .map(Vec::as_slice)
        .map_err(Clone::clone)
}

fn load_registry_entries() -> Result<Vec<SurfaceEntry>, String> {
    let mut entries = Vec::new();
    for width in 1u8..=11 {
        let source = domain_table_source(width)
            .map_err(|error| format!("D{width}: не вдалося отримати таблицю проєкцій: {error}"))?;
        let forms = parse(&source).map_err(|error| {
            format!(
                "не вдалося розібрати таблицю D{width}: {}",
                error.render(&source)
            )
        })?;
        let root = forms
            .first()
            .and_then(expr_list)
            .ok_or_else(|| format!("D{width}: очікувався корінь domain-table-1"))?;
        if root.first().and_then(expr_symbol) != Some("domain-table-1") {
            return Err(format!("D{width}: невідомий формат таблиці"));
        }
        for row in root.iter().skip(1) {
            let row_fields = expr_list(row)
                .ok_or_else(|| format!("D{width}: рядок таблиці має бути списком"))?;
            let key = row_fields
                .first()
                .ok_or_else(|| format!("D{width}: порожній рядок"))?;
            let bits = source
                .get(key.span.start..key.span.end)
                .ok_or_else(|| format!("D{width}: некоректний діапазон ключа"))?;
            if bits.len() != usize::from(width)
                || !bits.bytes().all(|bit| matches!(bit, b'0' | b'1'))
            {
                return Err(format!(
                    "D{width}: ключ {bits:?} не має точної ширини домену"
                ));
            }
            let mut names = FIXED_SURFACES
                .iter()
                .map(|surface| SurfaceName {
                    surface: (*surface).to_string(),
                    name: None,
                })
                .collect::<Vec<_>>();
            for field in row_fields.iter().skip(1) {
                let parts = expr_list(field)
                    .ok_or_else(|| format!("D{width}:{bits}: проєкція має бути списком"))?;
                if parts.len() != 2 {
                    return Err(format!("D{width}:{bits}: очікував пару назва/значення"));
                }
                let surface = expr_symbol(&parts[0])
                    .ok_or_else(|| format!("D{width}:{bits}: назва проєкції має бути символом"))?;
                let slot = names
                    .iter_mut()
                    .find(|slot| slot.surface == surface)
                    .ok_or_else(|| format!("D{width}:{bits}: невідома проєкція {surface}"))?;
                slot.name = projection_value(&parts[1]).map(str::to_string);
            }
            entries.push(SurfaceEntry {
                identity: format!("D{width}:{bits}"),
                names,
            });
        }
    }

    if entries.is_empty() {
        return Err("D1–D11 таблиці не містять жодної координати".to_string());
    }
    Ok(entries)
}

fn domain_table_source(width: u8) -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = crate::zig_transport::domain_table_source_bytes(width)?;
        String::from_utf8(bytes)
            .map_err(|error| format!("ZIG_DOMAIN_TABLE_CARRIER invalid UTF-8: {error}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err(format!(
            "RUST_ZIG_ONLY: domain table D{width} requires Zig; no Rust source fallback"
        ))
    }
}

fn projection_value(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::Symbol(value) | ExprKind::String(value) => Some(value.as_ref()),
        ExprKind::List(items) if items.is_empty() => None,
        _ => None,
    }
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

fn find_entries<'a>(entries: &'a [SurfaceEntry], requested: &str) -> Vec<&'a SurfaceEntry> {
    entries
        .iter()
        .filter(|entry| {
            entry.identity == requested
                || entry
                    .names
                    .iter()
                    .any(|surface| surface.name.as_deref() == Some(requested))
        })
        .collect()
}

// Repeated lookups during a real T5M mint must be constant-time even for large
// Lisp libraries; every entry remains owned by the exact Dn coordinate.
type SurfaceIndex = HashMap<(String, String), Option<String>>;

static SURFACE_INDEX: OnceLock<Result<SurfaceIndex, String>> = OnceLock::new();
static UKR_INDEX: OnceLock<Result<HashMap<String, String>, String>> = OnceLock::new();

fn surface_index() -> Result<&'static SurfaceIndex, String> {
    SURFACE_INDEX
        .get_or_init(|| {
            let mut index = HashMap::new();
            for entry in registry_entries()? {
                for name in &entry.names {
                    if let Some(spelling) = name.name.as_ref() {
                        let key = (name.surface.clone(), spelling.clone());
                        // Keep ambiguous names uncallable; do not assign arbitrary
                        // priority to one of two distinct exact domains.
                        match index.entry(key) {
                            std::collections::hash_map::Entry::Vacant(slot) => {
                                slot.insert(Some(entry.identity.clone()));
                            }
                            std::collections::hash_map::Entry::Occupied(mut slot) => {
                                *slot.get_mut() = None;
                            }
                        }
                    }
                }
            }
            Ok(index)
        })
        .as_ref()
        .map_err(Clone::clone)
}

fn ukr_index() -> Result<&'static HashMap<String, String>, String> {
    UKR_INDEX
        .get_or_init(|| {
            let mut index = HashMap::new();
            for entry in registry_entries()? {
                if let Some(name) = surface_name(entry, "укр").and_then(|name| name.name.as_ref())
                {
                    index.insert(entry.identity.clone(), name.clone());
                }
            }
            Ok(index)
        })
        .as_ref()
        .map_err(Clone::clone)
}

/// Resolve a spelling only in the selected projection column. Ambiguous names
/// fail closed; the returned coordinate is still only a table projection, not
/// proof that the resident is callable.
pub(super) fn identity_for_surface_name(
    surface: &str,
    requested: &str,
) -> Result<Option<String>, String> {
    let key = (normalize_surface(surface).to_owned(), requested.to_owned());
    Ok(surface_index()?.get(&key).cloned().flatten())
}

/// Return the full Ukrainian spelling paired with one exact table identity.
pub(super) fn ukr_name_for_identity(identity: &str) -> Result<Option<String>, String> {
    Ok(ukr_index()?.get(identity).cloned())
}

/// Return one exact projection spelling for a known table identity.
pub(super) fn name_for_identity(surface: &str, identity: &str) -> Result<Option<String>, String> {
    Ok(registry_entries()?
        .iter()
        .find(|entry| entry.identity == identity)
        .and_then(|entry| surface_name(entry, surface))
        .and_then(|name| name.name.clone()))
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

#[cfg(test)]
fn expr_string(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::String(text) => Some(text.as_ref()),
        _ => None,
    }
}

/// Documentation key is an exact D1..D10 domain coordinate, not legacy SID8.
#[cfg(test)]
fn expr_documentation_key(expr: &Expr) -> Option<String> {
    let symbol = expr_symbol(expr)?;
    let (domain, bits) = symbol.split_once(':')?;
    let width = domain.strip_prefix('D')?.parse::<usize>().ok()?;
    if (1..=10).contains(&width)
        && bits.len() == width
        && bits.bytes().all(|bit| matches!(bit, b'0' | b'1'))
    {
        Some(symbol.to_string())
    } else {
        None
    }
}

#[cfg(test)]
fn uk_docs_source_zig_only() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = crate::zig_transport::uk_docs_source_bytes()?;
        String::from_utf8(bytes).map_err(|err| format!("ZIG_UK_DOCS_CARRIER invalid UTF-8: {err}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: uk-docs requires Zig; no Rust source fallback".into())
    }
}

#[cfg(test)]
fn ukrainian_docs() -> Result<Vec<SurfaceDoc>, String> {
    let source = uk_docs_source_zig_only()?;
    let program = parse(&source).map_err(|error| {
        format!(
            "не вдалося прочитати uk-docs.wsm: {}",
            error.render(&source)
        )
    })?;
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
            if fields.len() != 7 || fields.first().and_then(expr_symbol) != Some("doc") {
                return Err("uk-docs.wsm: некоректний doc-запис".to_string());
            }
            if expr_symbol(&fields[3]).is_none() {
                return Err("uk-docs.wsm: немає повної української проєкції".to_string());
            }
            Ok(SurfaceDoc {
                category: expr_symbol(&fields[1])
                    .ok_or_else(|| "uk-docs.wsm: category має бути символом".to_string())?
                    .to_string(),
                identity: expr_documentation_key(&fields[2]).ok_or_else(|| {
                    "uk-docs.wsm: потрібен точний домен D1–D10 з власною шириною".to_string()
                })?,
                kind: expr_symbol(&fields[4])
                    .ok_or_else(|| "uk-docs.wsm: kind має бути символом".to_string())?
                    .to_string(),
                call: expr_string(&fields[5])
                    .ok_or_else(|| "uk-docs.wsm: call має бути рядком".to_string())?
                    .to_string(),
                description: expr_string(&fields[6])
                    .ok_or_else(|| "uk-docs.wsm: description має бути рядком".to_string())?
                    .to_string(),
            })
        })
        .collect()
}

pub(crate) fn render_status() -> Result<String, String> {
    let entries = registry_entries()?;
    let denominator = public_denominator(entries);
    let uk = counts_for(entries, "ук");
    let en = counts_for(entries, "en");
    let ukr = counts_for(entries, "укр");
    let san = counts_for(entries, "san");
    let lisp = counts_for(entries, "LISP");
    let symbolic = entries
        .iter()
        .filter(|entry| {
            surface_name(entry, "sym")
                .and_then(|item| item.name.as_deref())
                .is_some()
        })
        .count();
    let four_projection_rows = entries
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
        "Проєкції таблиць D1–D11 · доменні координати: {denominator}\n\
         UK  present {:>3} · empty {:>3}\n\
         UKR present {:>3} · empty {:>3}\n\
         EN  present {:>3} · empty {:>3}\n\
         SAN present {:>3} · empty {:>3}\n\
         LISP present {:>3} · empty {:>3}\n\
         shared sym identities: {symbolic}\n\
         rows with all four human projections: {four_projection_rows}/{denominator}",
        uk.present,
        uk.empty,
        ukr.present,
        ukr.empty,
        en.present,
        en.empty,
        san.present,
        san.empty,
        lisp.present,
        lisp.empty,
    ))
}

pub(crate) fn render_names(surface: &str) -> Result<String, String> {
    let entries = registry_entries()?;
    if surface == "core" {
        let mut output = format!(
            "core: exact domain identities D1–D11 · {}\n",
            public_denominator(entries)
        );
        for (index, entry) in entries.iter().enumerate() {
            if index > 0 {
                output.push_str(if index % 12 == 0 { "\n" } else { " · " });
            }
            output.push_str(&entry.identity);
        }
        output
            .push_str("\n\ncore показує machine handles; людські назви дивіться через :ім'я <ID>.");
        return Ok(output);
    }

    let surface = normalize_surface(surface);
    let counts = counts_for(entries, surface);
    let mut output = format!(
        "surface {surface}: present {} · empty {} · total {}\n  ",
        counts.present,
        counts.empty,
        entries.len()
    );
    let mut first = true;
    for entry in entries {
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
    let matches = find_entries(entries, requested);
    if matches.is_empty() {
        return Ok(format!(
            "«{requested}» не знайдено серед координат таблиць D1–D11; викличність з цього каталогу не випливає."
        ));
    };

    if matches.len() > 1 {
        let identities = matches
            .iter()
            .map(|entry| entry.identity.as_str())
            .collect::<Vec<_>>()
            .join(", ");
        return Ok(format!(
            "«{requested}» неоднозначне; уточніть домен: {identities}"
        ));
    }
    let entry = matches[0];

    let mut output = format!(
        "identity: {}\n  UK: {}\n  UKR: {}\n  EN: {}\n  SAN: {}\n  LISP: {}\n  SYM: {}",
        entry.identity,
        rendered_name(surface_name(entry, "ук")),
        rendered_name(surface_name(entry, "укр")),
        rendered_name(surface_name(entry, "en")),
        rendered_name(surface_name(entry, "san")),
        rendered_name(surface_name(entry, "LISP")),
        rendered_name(surface_name(entry, "sym")),
    );
    output.push_str("\n  current: ");
    output.push_str(surface);

    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[cfg(feature = "zig-transport")]
    #[test]
    fn domain_and_exact_bits_are_the_identity() {
        let entries = registry_entries().expect("byte registry");
        for width in 1..=11 {
            assert!(
                entries
                    .iter()
                    .any(|entry| entry.identity.starts_with(&format!("D{width}:"))),
                "missing D{width} rows"
            );
        }
        let d11_count = entries
            .iter()
            .filter(|entry| entry.identity.starts_with("D11:"))
            .count();
        assert!(
            d11_count >= 512,
            "test_id=D11_REPL_TABLE_COUNT layer=projection input=D11 expected=at-least-512-derived actual={d11_count}"
        );
        assert_eq!(find_entries(entries, "D3:010")[0].identity, "D3:010");
        assert!(
            find_entries(entries, "010").is_empty(),
            "bits alone are not global identity"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn all_projection_columns_come_from_domain_tables() {
        let entries = registry_entries().expect("numeric registry");
        let entry = find_entries(entries, "D3:010")[0];
        assert_eq!(
            surface_name(entry, "ук").and_then(|item| item.name.as_deref()),
            Some("атом?")
        );
        assert_eq!(
            surface_name(entry, "LISP").and_then(|item| item.name.as_deref()),
            Some("ATOM")
        );
        assert_eq!(normalize_surface("sa"), "san");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn repl_never_reports_a_human_spelling_as_identity() {
        let output = render_name("ук", "D3:010").expect("render D3 identity");
        assert!(output.starts_with("identity: D3:010\n"));
        assert!(output.contains("UK: атом?"));
        assert!(output.contains("LISP: ATOM"));
    }

    // Included in the existing automatic CI "zig_linter_carrier" test filter:
    // this exercises actual Rust -> Zig FFI -> SENS-owned parser, not a mock.
    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_linter_carrier_uk_docs_exact_bytes_and_sens_owned_parse() {
        let bytes = crate::zig_transport::uk_docs_source_bytes()
            .expect("Zig root ABI must return UK docs bytes");
        let source = uk_docs_source_zig_only().expect("Rust must obtain UK docs only through Zig");
        assert!(!bytes.is_empty(), "Zig must not return an empty asset");
        assert_eq!(
            source.as_bytes(),
            bytes.as_slice(),
            "every byte must survive Zig ABI"
        );
        // SENS owns the parser/identities; this is not semantic admission by Zig.
        let docs = ukrainian_docs().expect("SENS parses Zig-delivered documentation");
        assert!(
            docs.iter().any(|doc| doc.identity == "D3:001"),
            "expected exact D3 domain documentation identity"
        );
        println!(
            "ZIG_UK_DOCS_CARRIER_PASS test_id=zig-uk-docs-exact-carry \
             layer=transport bytes={} semantic_authority=SENS \
             semantic_admission=NOT_TESTED",
            bytes.len()
        );
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn zig_linter_carrier_uk_docs_refuses_without_zig() {
        let error = uk_docs_source_zig_only()
            .expect_err("Rust must not embed/read the SENS UK docs source");
        assert!(
            error.contains("RUST_ZIG_ONLY: uk-docs requires Zig; no Rust source fallback"),
            "unexpected denial: {error}"
        );
        let domain_error =
            domain_table_source(1).expect_err("Rust must not embed/read domain tables");
        assert!(
            domain_error.contains("RUST_ZIG_ONLY: domain table D1 requires Zig"),
            "unexpected domain-table denial: {domain_error}"
        );
        println!(
            "ZIG_UK_DOCS_NO_FALLBACK_PASS test_id=zig-uk-docs-deny-no-zig \
             layer=transport semantic_authority=SENS"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn core_catalog_lists_domain_qualified_identities() {
        let output = render_names("core").expect("core catalog");
        assert!(output.contains("D1:0"));
        assert!(output.contains("D11:01100000000"));
        assert!(!output.contains("byte semantic"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn projection_spelling_resolves_only_when_unique() {
        let entries = registry_entries().expect("domain registry");
        let candidates = find_entries(entries, "так");
        let output = render_name("ук", "так").expect("ambiguity is user-visible");
        assert_eq!(candidates.len(), 1);
        assert!(output.starts_with("identity: D1:1\n"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn repl_surface_catalog_projects_the_current_derived_d11_table_row() {
        let output = render_name("укр", "D11:01100000000").expect("D11 projection");
        assert!(
            output.starts_with("identity: D11:01100000000\n"),
            "test_id=D11_REPL_DERIVED_PROJECTION layer=projection input=D11:01100000000 expected=current-derived-selector actual={output}"
        );
        assert!(output.contains("LISP: CDAAAAAAAAR"), "{output}");
        assert!(output.contains("EN: cdaaaaaaaar"), "{output}");
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn domain_table_bytes_are_carried_by_zig_then_parsed_by_sens() {
        for width in 1..=11 {
            let bytes = crate::zig_transport::domain_table_source_bytes(width)
                .expect("Zig should return the exact table bytes");
            let source = domain_table_source(width).expect("SENS source route");
            assert!(!bytes.is_empty(), "D{width} table must not be empty");
            assert_eq!(bytes, source.as_bytes(), "D{width} bytes must remain exact");
            let forms = parse(&source).expect("SENS parser owns source interpretation");
            let root = forms
                .first()
                .and_then(expr_list)
                .expect("SENS parser returns a domain table root");
            assert_eq!(
                root.first().and_then(expr_symbol),
                Some("domain-table-1"),
                "D{width} table root must be parsed by SENS"
            );
        }
        assert!(crate::zig_transport::domain_table_source_bytes(0)
            .expect_err("invalid asset selector must fail closed")
            .contains("unknown asset index"));
    }
}
