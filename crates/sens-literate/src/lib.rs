use sens::{eval_parsed_expressions, parse, parse_canonical, EvalResult, Expr, LanguageError, Session};
use pulldown_cmark::{CodeBlockKind, Event, Parser, Tag, TagEnd};

/// Remaps a concatenated string offset back to the original source file offset.
/// Public so callers that need to run their OWN analysis over the
/// concatenated code (e.g. sens-wasm's diagnose(), which shares
/// sens-lsp's canonical arity_diagnostics() instead of duplicating
/// diagnostic logic) can remap those results too, not just the
/// parse/eval errors this module already handles internally.
pub fn remap_offset(offset: usize, maps: &[(usize, usize, usize)]) -> usize {
    for &(concat_start, concat_end, orig_start) in maps {
        if offset >= concat_start && offset < concat_end {
            return orig_start + (offset - concat_start);
        }
    }
    // Fallback: if offset is exactly at the end of the last block
    if let Some(&(concat_start, concat_end, orig_start)) = maps.last() {
        if offset == concat_end {
            return orig_start + (offset - concat_start);
        }
    }
    offset
}

fn remap_error(mut error: LanguageError, maps: &[(usize, usize, usize)]) -> LanguageError {
    error.span.start = remap_offset(error.span.start, maps);
    error.span.end = remap_offset(error.span.end, maps);
    error
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SourceMode {
    PureLisp,
    Literate,
}

pub fn extract_code(source: &str, is_literate: bool) -> (String, Vec<(usize, usize, usize)>) {
    if !is_literate {
        return (source.to_string(), vec![(0, source.len(), 0)]);
    }

    let mut concatenated = String::new();
    let mut offset_maps = Vec::new();
    let parser = Parser::new(source).into_offset_iter();
    let mut in_sens_block = false;

    for (event, range) in parser {
        match event {
            Event::Start(Tag::CodeBlock(CodeBlockKind::Fenced(lang)))
                if lang.as_ref() == "sens" =>
            {
                in_sens_block = true;
            }
            Event::End(TagEnd::CodeBlock) if in_sens_block => {
                in_sens_block = false;
            }
            Event::Text(text) if in_sens_block => {
                let concat_start = concatenated.len();
                concatenated.push_str(&text);
                let concat_end = concatenated.len();
                offset_maps.push((concat_start, concat_end, range.start));
            }
            _ => {}
        }
    }
    (concatenated, offset_maps)
}

pub fn parse_literate(source: &str, mode: SourceMode) -> Result<Vec<Expr>, LanguageError> {
    let (concatenated, offset_maps) = extract_code(source, mode == SourceMode::Literate);

    if mode == SourceMode::Literate && offset_maps.is_empty() {
        return Ok(vec![]);
    }

    parse(&concatenated).map_err(|e| remap_error(e, &offset_maps))
}


/// Canonical binary counterpart to `parse_literate`.
///
/// Markdown extraction is identical; only the language reader differs. This
/// keeps one default SENS source law across file, native REPL and Web/WASM.
pub fn parse_literate_canonical(
    source: &str,
    mode: SourceMode,
) -> Result<Vec<Expr>, LanguageError> {
    let (concatenated, offset_maps) = extract_code(source, mode == SourceMode::Literate);

    if mode == SourceMode::Literate && offset_maps.is_empty() {
        return Ok(vec![]);
    }

    parse_canonical(&concatenated).map_err(|e| remap_error(e, &offset_maps))
}

pub fn eval_literate(
    source: &str,
    mode: SourceMode,
    session: &mut Session,
) -> Result<(EvalResult, Vec<Expr>), LanguageError> {
    let (concatenated, offset_maps) = extract_code(source, mode == SourceMode::Literate);

    if mode == SourceMode::Literate && offset_maps.is_empty() {
        return Ok((
            EvalResult {
                value: sens::Value::Nil,
                output: vec!["No sens code blocks found in markdown document.".to_string()],
            },
            vec![],
        ));
    }

    let forms = parse(&concatenated).map_err(|e| remap_error(e, &offset_maps))?;

    // Canonical bootstrap order: language-owned macro layer first, then core.my.
    sens::load_core_library(session).map_err(|e| remap_error(e, &offset_maps))?;

    let result =
        eval_parsed_expressions(&forms, session).map_err(|e| remap_error(e, &offset_maps))?;
    Ok((result, forms))
}


/// Evaluate literate/pure source through the canonical binary SENS reader.
///
/// This is the default interactive/browser path. Human surface entrypoints use
/// `eval_literate` explicitly instead.
pub fn eval_literate_canonical(
    source: &str,
    mode: SourceMode,
    session: &mut Session,
) -> Result<(EvalResult, Vec<Expr>), LanguageError> {
    let (concatenated, offset_maps) = extract_code(source, mode == SourceMode::Literate);

    if mode == SourceMode::Literate && offset_maps.is_empty() {
        return Ok((
            EvalResult {
                value: sens::Value::Nil,
                output: vec!["No sens code blocks found in markdown document.".to_string()],
            },
            vec![],
        ));
    }

    let forms = parse_canonical(&concatenated).map_err(|e| remap_error(e, &offset_maps))?;

    sens::load_core_library(session).map_err(|e| remap_error(e, &offset_maps))?;

    let result =
        eval_parsed_expressions(&forms, session).map_err(|e| remap_error(e, &offset_maps))?;
    Ok((result, forms))
}
