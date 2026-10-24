// GENERATED from contracts/numeric-domains-ratification.lisp — DO NOT EDIT BY HAND.
// Чинний D12+ закон: D(12 * 2^n), n >= 0.
// Rust переносить точні ширини, а не визначає семантику або виконання.

/// Початковий префікс ратифікованих математичних ширин.
pub const NUMERIC_DOMAIN_WIDTHS: [u16; 5] = [ 12, 24, 48, 96, 192 ];
pub const FIRST_NUMERIC_DOMAIN_WIDTH: u16 = 12;

/// Реально підтримуваний фізичний профіль, без D12.
pub const PHYSICAL_NUMERIC_WIDTHS: [u16; 4] = [ 24, 48, 96, 192 ];
pub const FIRST_PHYSICAL_NUMERIC_WIDTH: u16 = 24;

/// Подвоєння ширини не надає права виклику чи фізичної підтримки.
pub const fn next_width(w: u16) -> u16 { w * 2 }
