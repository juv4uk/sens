//! Канонічна ємність Рамки-3 із законом форми.
//!
//! Цей модуль містить досліджені таблиці ємності як специфікацію для
//! універсального кодека (#5439). Таблиці згенеровано Python-скриптом
//! `research/framed3/canonical_capacity_research.py` та валідовані проти
//! незалежного оракула `definitely_impossible`.
//!
//! Закон форми (власник, 11.10.2026):
//! 1. Слово-голова: argc = арність (таблиця насінь; COND — з клаузами).
//! 2. Підформа-голова: лише LAMBDA (координата UNRESOLVED у D3).
//! 3. Аргумент QUOTE — дані: будь-яке дерево, без арностей.
//!
//! `()` — це D3-слово `000`, а не порожній D2-кадр.

/// Профіль коду: визначає, які підформи-голови дозволені.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FormProfile {
    /// D3-PROFILE (мова насінь): підформи-голови заборонені.
    D3Profile,
    /// ПОВНИЙ PROFILE: підформа-голова дозволена, якщо її голова — LAMBDA.
    FullProfile,
}

/// Таблиця ємності: (n, structural, canonical, strict).
///
/// n — трит-довжина; structural — без закону форми; canonical — закон арності;
/// strict — підформа-голова лише LAMBDA (UNRESOLVED → відкидається).
pub const CAPACITY_TABLES: &[(u32, u64, u64, u64)] = &[
    (4, 1, 0, 0),
    (5, 2, 2, 2),
    (6, 1, 0, 0),
    (7, 12, 6, 6),
    (8, 20, 20, 20),
    (9, 74, 68, 68),
    (10, 160, 148, 148),
    (11, 476, 440, 438),
    (12, 1196, 1148, 1148),
    (13, 3344, 3053, 3043),
    (14, 7620, 7072, 7048),
    (15, 21521, 19473, 19368),
    (16, 53712, 48541, 48293),
    (17, 147886, 131960, 131116),
    (18, 374510, 333409, 331080),
    (19, 994900, 874816, 867750),
    (20, 2553514, 2241222, 2222296),
    (21, 6719833, 5831187, 5775068),
    (22, 17354464, 15043687, 14891451),
    (23, 45407508, 39065169, 38623781),
    (24, 117602440, 101049990, 99845048),
    (25, 307615800, 263226389, 259839773),
    (26, 799215440, 682964203, 673712967),
    (27, 2087049147, 1779181018, 1753547526),
];

/// Структурна ємність для даної трит-довжини.
pub fn structural_capacity(n: u32) -> Option<u64> {
    CAPACITY_TABLES
        .iter()
        .find(|(len, _, _, _)| *len == n)
        .map(|(_, s, _, _)| *s)
}

/// Канонічна ємність для даної трит-довжини та профілю.
pub fn canonical_capacity(n: u32, profile: FormProfile) -> Option<u64> {
    CAPACITY_TABLES
        .iter()
        .find(|(len, _, _, _)| *len == n)
        .map(|(_, _, c, s)| match profile {
            FormProfile::D3Profile => *s,
            FormProfile::FullProfile => *c,
        })
}

/// Розмір блоку в байтах для даної трит-довжини.
pub fn block_size(n: u32) -> u32 {
    if n <= 8 {
        1
    } else if n <= 14 {
        2
    } else if n <= 20 {
        3
    } else if n <= 26 {
        4
    } else if n <= 32 {
        5
    } else {
        6
    }
}

// ------------------------------------------------------------------ дерево

#[derive(Clone, Debug, PartialEq, Eq)]
enum Node<'a> {
    Word(&'a str),
    Form(Vec<Node<'a>>),
}

/// Перевірка канонічної валідності послідовності слів.
///
/// Повертає true, якщо послідовність є валідною програмою за законом форми
/// у даному профілі.
pub fn is_canonical_form(words: &[&str], profile: FormProfile) -> bool {
    let mut pos = 0;
    match parse_program(words, &mut pos) {
        Some(tree) if pos == words.len() => check_form(&tree, profile, false),
        _ => false,
    }
}

fn parse_program<'a>(words: &[&'a str], pos: &mut usize) -> Option<Node<'a>> {
    if *pos >= words.len() || words[*pos] != "10" {
        return None;
    }
    *pos += 1;
    parse_list(words, pos)
}

fn parse_list<'a>(words: &[&'a str], pos: &mut usize) -> Option<Node<'a>> {
    let mut items = Vec::new();
    let mut heads = 0usize;
    loop {
        while *pos < words.len() && words[*pos] == "00" {
            *pos += 1;
        }
        if *pos >= words.len() {
            return None;
        }
        let word = words[*pos];
        if word == "01" {
            *pos += 1;
            return Some(Node::Form(items));
        }
        if word == "11" {
            if heads == 0 {
                return None;
            }
            *pos += 1;
            while *pos < words.len() && words[*pos] == "00" {
                *pos += 1;
            }
            let tail = parse_expression(words, pos)?;
            while *pos < words.len() && words[*pos] == "00" {
                *pos += 1;
            }
            if *pos >= words.len() || words[*pos] != "01" {
                return None;
            }
            *pos += 1;
            items.push(tail);
            return Some(Node::Form(items));
        }
        let expr = parse_expression(words, pos)?;
        items.push(expr);
        heads += 1;
    }
}

fn parse_expression<'a>(words: &[&'a str], pos: &mut usize) -> Option<Node<'a>> {
    if *pos >= words.len() {
        return None;
    }
    let word = words[*pos];
    if word == "10" {
        return parse_program(words, pos);
    }
    if word.len() == 2 {
        return None;
    }
    *pos += 1;
    Some(Node::Word(word))
}

// ------------------------------------------------------------------ закон форми

fn check_form(node: &Node<'_>, profile: FormProfile, data: bool) -> bool {
    match node {
        Node::Word(_) => true,
        Node::Form(items) => {
            if items.is_empty() {
                // () = 000, не порожній кадр. У даних — допустимо.
                return data;
            }
            if data {
                return items.iter().all(|item| check_form(item, profile, true));
            }
            let head = &items[0];
            let args = &items[1..];
            let known_arity = match head {
                Node::Word("001") => Some(1),
                Node::Word("010") | Node::Word("011") | Node::Word("100") => Some(1),
                Node::Word("101") | Node::Word("111") => Some(2),
                _ => None,
            };
            match head {
                Node::Word(_) if known_arity == Some(args.len()) => {
                    // Правильна арність. QUOTE — дані, інші — код.
                    let data = matches!(head, Node::Word("001"));
                    args.iter().all(|a| check_form(a, profile, data))
                }
                Node::Word("000" | "110") => {
                    // EMPTY, COND — без фіксованої арності.
                    args.iter().all(|a| check_form(a, profile, false))
                }
                Node::Word(_) => false, // Неправильна арність — мертве дерево.
                Node::Form(_) => {
                    // Підформа-голова.
                    match profile {
                        FormProfile::D3Profile => false,
                        FormProfile::FullProfile => {
                            // LAMBDA UNRESOLVED — консервативно допускаємо.
                            check_form(head, profile, false)
                                && args.iter().all(|a| check_form(a, profile, false))
                        }
                    }
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn capacity_tables_match_python() {
        assert_eq!(structural_capacity(4), Some(1));
        assert_eq!(structural_capacity(7), Some(12));
        assert_eq!(structural_capacity(14), Some(7620));
        assert_eq!(canonical_capacity(7, FormProfile::D3Profile), Some(6));
        assert_eq!(canonical_capacity(14, FormProfile::FullProfile), Some(7072));
    }

    #[test]
    fn block_size_correct() {
        assert_eq!(block_size(4), 1);
        assert_eq!(block_size(8), 1);
        assert_eq!(block_size(9), 2);
        assert_eq!(block_size(14), 2);
        assert_eq!(block_size(15), 3);
        assert_eq!(block_size(20), 3);
        assert_eq!(block_size(21), 4);
        assert_eq!(block_size(26), 4);
        assert_eq!(block_size(27), 5);
        assert_eq!(block_size(32), 5);
        assert_eq!(block_size(33), 6);
    }

    #[test]
    fn dead_tree_rejected() {
        let dead = ["10", "10", "010", "01", "01"]; // ((ATOM))
        assert!(!is_canonical_form(&dead, FormProfile::D3Profile));
        assert!(!is_canonical_form(&dead, FormProfile::FullProfile));
    }

    #[test]
    fn quoted_data_preserved() {
        let quoted = ["10", "001", "10", "010", "01", "01"]; // (QUOTE ((ATOM)))
        assert!(is_canonical_form(&quoted, FormProfile::D3Profile));
        assert!(is_canonical_form(&quoted, FormProfile::FullProfile));
    }

    #[test]
    fn empty_frame_rejected() {
        let empty = ["10", "01"]; // () = 000, не кадр
        assert!(!is_canonical_form(&empty, FormProfile::D3Profile));
    }

    #[test]
    fn valid_forms_accepted() {
        let atom = ["10", "010", "0", "01"]; // (ATOM 0)
        assert!(is_canonical_form(&atom, FormProfile::D3Profile));
        let cons = ["10", "111", "0", "1", "01"]; // (CONS 0 1)
        assert!(is_canonical_form(&cons, FormProfile::D3Profile));
    }

    #[test]
    fn arity_mismatch_rejected() {
        let no_arg = ["10", "010", "01"]; // (ATOM) — 0 аргументів
        assert!(!is_canonical_form(&no_arg, FormProfile::D3Profile));
        let two_args = ["10", "010", "0", "1", "01"]; // (ATOM 0 1) — 2 аргументи
        assert!(!is_canonical_form(&two_args, FormProfile::D3Profile));
    }
}
