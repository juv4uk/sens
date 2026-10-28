//! Dense Frame3-Micro enumerator for 1/2/3/4-byte payloads plus prefix-stable F3M-5.
//!
//! Canonical order is over a deliberately total, closed D3 microgrammar:
//! literals 0/1/NIL, QUOTE of those literals, ATOM, CONS,
//! CAR(CONS(...)), CDR(CONS(...)), and a total IF-ATOM expansion through
//! exact D3 COND. Every constructor is chosen so decoded programs are closed
//! and do not require host names or dynamic bindings.
//!
//! The global enumeration is ordered first by expression node count, then by
//! constructor/split/rank order. Physical profiles are disjoint windows:
//!   F3M-1 = global ranks [0, 256)
//!   F3M-2 = next 65_536 ranks
//!   F3M-3 = next 16_777_216 ranks
//!   F3M-4 = next 4_294_967_296 legacy ranks
//!   F3M-5 = independent 2^40 extension ranks containing EQ and/or LAMBDA
//! Thus every payload value in each admitted width names exactly one program,
//! with no reserved/magic code points and no aliases across widths.

use crate::frame3_micro::{frame3_micro_profile, Frame3MicroProfile};

const LEAF_COUNT: u128 = 6;
const F3M1_CAPACITY: u128 = 1u128 << 8;
const F3M2_CAPACITY: u128 = 1u128 << 16;
const F3M3_CAPACITY: u128 = 1u128 << 24;
const F3M4_CAPACITY: u128 = 1u128 << 32;
const F3M5_CAPACITY: u128 = crate::frame3_micro_v5::F3M5_CAPACITY;
const F3M2_OFFSET: u128 = F3M1_CAPACITY;
const F3M3_OFFSET: u128 = F3M1_CAPACITY + F3M2_CAPACITY;
const F3M4_OFFSET: u128 = F3M3_OFFSET + F3M3_CAPACITY;
const F3M_END: u128 = F3M4_OFFSET + F3M4_CAPACITY;
const COUNT_LIMIT: usize = 16;

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum Frame3MicroExpr {
    Zero,
    One,
    Nil,
    QuoteZero,
    QuoteOne,
    QuoteNil,
    Atom(Box<Frame3MicroExpr>),
    Cons(Box<Frame3MicroExpr>, Box<Frame3MicroExpr>),
    CarCons(Box<Frame3MicroExpr>, Box<Frame3MicroExpr>),
    CdrCons(Box<Frame3MicroExpr>, Box<Frame3MicroExpr>),
    /// Total D3 EQ witness: EQ is applied only to exact-D1 ATOM results.
    EqAtom(Box<Frame3MicroExpr>, Box<Frame3MicroExpr>),
    /// D4 LAMBDA with an empty parameter list and a closed body.
    Lambda0(Box<Frame3MicroExpr>),
    /// Total conditional:
    /// (COND ((ATOM test) then) (1 else))
    IfAtom(
        Box<Frame3MicroExpr>,
        Box<Frame3MicroExpr>,
        Box<Frame3MicroExpr>,
    ),
}

pub const CAP_QUOTE: u8 = 1 << 0;
pub const CAP_ATOM: u8 = 1 << 1;
pub const CAP_CONS: u8 = 1 << 2;
pub const CAP_CAR: u8 = 1 << 3;
pub const CAP_CDR: u8 = 1 << 4;
pub const CAP_COND: u8 = 1 << 5;
pub const CAP_EQ: u8 = 1 << 6;
pub const CAP_LAMBDA: u8 = 1 << 7;
/// Frozen six-capability mask used by F3M-1..4 proofs.
pub const CAP_ALL: u8 = CAP_QUOTE | CAP_ATOM | CAP_CONS | CAP_CAR | CAP_CDR | CAP_COND;
/// F3M-5 adds the missing D3 EQ capability plus D4 LAMBDA.
pub const CAP_ALL_F3M5: u8 = CAP_ALL | CAP_EQ | CAP_LAMBDA;

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Frame3MicroEnumerateError {
    UnsupportedLength(usize),
    RankOutOfRange,
    ProgramOutsideF3M4,
    InternalCountOverflow,
}

impl std::fmt::Display for Frame3MicroEnumerateError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{self:?}")
    }
}

impl std::error::Error for Frame3MicroEnumerateError {}

impl Frame3MicroExpr {
    pub fn node_count(&self) -> usize {
        match self {
            Self::Zero
            | Self::One
            | Self::Nil
            | Self::QuoteZero
            | Self::QuoteOne
            | Self::QuoteNil => 1,
            Self::Atom(value) | Self::Lambda0(value) => 1 + value.node_count(),
            Self::Cons(left, right)
            | Self::CarCons(left, right)
            | Self::CdrCons(left, right)
            | Self::EqAtom(left, right) => 1 + left.node_count() + right.node_count(),
            Self::IfAtom(test, then_value, else_value) => {
                1 + test.node_count() + then_value.node_count() + else_value.node_count()
            }
        }
    }

    pub fn exact_words(&self) -> Vec<&'static str> {
        match self {
            Self::Zero => vec!["0"],
            Self::One => vec!["1"],
            Self::Nil => vec!["000"],
            Self::QuoteZero => unary_call("001", vec!["0"]),
            Self::QuoteOne => unary_call("001", vec!["1"]),
            Self::QuoteNil => unary_call("001", vec!["000"]),
            Self::Atom(value) => unary_call("010", value.exact_words()),
            Self::Cons(left, right) => binary_call("111", left.exact_words(), right.exact_words()),
            Self::CarCons(left, right) => unary_call(
                "100",
                binary_call("111", left.exact_words(), right.exact_words()),
            ),
            Self::CdrCons(left, right) => unary_call(
                "011",
                binary_call("111", left.exact_words(), right.exact_words()),
            ),
            Self::EqAtom(left, right) => binary_call(
                "101",
                unary_call("010", left.exact_words()),
                unary_call("010", right.exact_words()),
            ),
            Self::Lambda0(body) => lambda0_call(body.exact_words()),
            Self::IfAtom(test, then_value, else_value) => {
                let predicate = unary_call("010", test.exact_words());
                let first_clause = list2(predicate, then_value.exact_words());
                let second_clause = list2(vec!["1"], else_value.exact_words());
                let mut out = vec!["10", "110"];
                out.extend(first_clause);
                out.extend(second_clause);
                out.push("01");
                out
            }
        }
    }

    pub fn human_projection(&self) -> String {
        match self {
            Self::Zero => "0".into(),
            Self::One => "1".into(),
            Self::Nil => "NIL".into(),
            Self::QuoteZero => "QUOTE(0)".into(),
            Self::QuoteOne => "QUOTE(1)".into(),
            Self::QuoteNil => "QUOTE(NIL)".into(),
            Self::Atom(value) => format!("ATOM({})", value.human_projection()),
            Self::Cons(left, right) => {
                format!(
                    "CONS({},{})",
                    left.human_projection(),
                    right.human_projection()
                )
            }
            Self::CarCons(left, right) => format!(
                "CAR(CONS({},{}))",
                left.human_projection(),
                right.human_projection()
            ),
            Self::CdrCons(left, right) => format!(
                "CDR(CONS({},{}))",
                left.human_projection(),
                right.human_projection()
            ),
            Self::EqAtom(left, right) => format!(
                "EQ(ATOM({}),ATOM({}))",
                left.human_projection(),
                right.human_projection()
            ),
            Self::Lambda0(body) => format!("LAMBDA((),{})", body.human_projection()),
            Self::IfAtom(test, then_value, else_value) => format!(
                "IF-ATOM({},{},{})",
                test.human_projection(),
                then_value.human_projection(),
                else_value.human_projection()
            ),
        }
    }

    /// Semantic constructor classes exercised by this closed micro-program.
    ///
    /// CAR(CONS(...)) and CDR(CONS(...)) count both the selector and CONS,
    /// while IF-ATOM counts COND; its exact expansion also contains ATOM.
    pub fn capability_mask(&self) -> u8 {
        match self {
            Self::Zero | Self::One | Self::Nil => 0,
            Self::QuoteZero | Self::QuoteOne | Self::QuoteNil => CAP_QUOTE,
            Self::Atom(value) => CAP_ATOM | value.capability_mask(),
            Self::Cons(left, right) => CAP_CONS | left.capability_mask() | right.capability_mask(),
            Self::CarCons(left, right) => {
                CAP_CAR | CAP_CONS | left.capability_mask() | right.capability_mask()
            }
            Self::CdrCons(left, right) => {
                CAP_CDR | CAP_CONS | left.capability_mask() | right.capability_mask()
            }
            Self::EqAtom(left, right) => {
                CAP_EQ | CAP_ATOM | left.capability_mask() | right.capability_mask()
            }
            Self::Lambda0(body) => CAP_LAMBDA | body.capability_mask(),
            Self::IfAtom(test, then_value, else_value) => {
                CAP_COND
                    | CAP_ATOM
                    | test.capability_mask()
                    | then_value.capability_mask()
                    | else_value.capability_mask()
            }
        }
    }
}

fn unary_call(head: &'static str, argument: Vec<&'static str>) -> Vec<&'static str> {
    let mut out = vec!["10", head];
    out.extend(argument);
    out.push("01");
    out
}

fn binary_call(
    head: &'static str,
    left: Vec<&'static str>,
    right: Vec<&'static str>,
) -> Vec<&'static str> {
    let mut out = vec!["10", head];
    out.extend(left);
    out.extend(right);
    out.push("01");
    out
}

fn list2(left: Vec<&'static str>, right: Vec<&'static str>) -> Vec<&'static str> {
    let mut out = vec!["10"];
    out.extend(left);
    out.extend(right);
    out.push("01");
    out
}

fn lambda0_call(body: Vec<&'static str>) -> Vec<&'static str> {
    // (LAMBDA () body) where the empty parameter list is structural D2 framing,
    // not the D3 NIL resident used as a value expression.
    let mut out = vec!["10", "0010", "10", "01"];
    out.extend(body);
    out.push("01");
    out
}

fn count_table() -> Result<[u128; COUNT_LIMIT + 1], Frame3MicroEnumerateError> {
    let mut counts = [0u128; COUNT_LIMIT + 1];
    counts[1] = LEAF_COUNT;
    for nodes in 2..=COUNT_LIMIT {
        let mut total = counts[nodes - 1]; // ATOM

        let mut binary_pairs = 0u128;
        for left_nodes in 1..nodes - 1 {
            let right_nodes = nodes - 1 - left_nodes;
            binary_pairs = binary_pairs
                .checked_add(
                    counts[left_nodes]
                        .checked_mul(counts[right_nodes])
                        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                )
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
        }
        total = total
            .checked_add(
                binary_pairs
                    .checked_mul(3)
                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
            )
            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;

        for test_nodes in 1..nodes.saturating_sub(2) {
            for then_nodes in 1..nodes - 1 - test_nodes {
                let else_nodes = nodes - 1 - test_nodes - then_nodes;
                if else_nodes == 0 {
                    continue;
                }
                let block = counts[test_nodes]
                    .checked_mul(counts[then_nodes])
                    .and_then(|value| value.checked_mul(counts[else_nodes]))
                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
                total = total
                    .checked_add(block)
                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
            }
        }
        counts[nodes] = total;
    }
    Ok(counts)
}

pub fn exact_node_capacity(nodes: usize) -> Result<u128, Frame3MicroEnumerateError> {
    let counts = count_table()?;
    counts
        .get(nodes)
        .copied()
        .filter(|value| *value != 0)
        .ok_or(Frame3MicroEnumerateError::RankOutOfRange)
}

fn cumulative_before(
    nodes: usize,
    counts: &[u128; COUNT_LIMIT + 1],
) -> Result<u128, Frame3MicroEnumerateError> {
    let mut total = 0u128;
    for value in counts.iter().take(nodes).skip(1) {
        total = total
            .checked_add(*value)
            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
    }
    Ok(total)
}

fn leaf_from_rank(rank: u128) -> Result<Frame3MicroExpr, Frame3MicroEnumerateError> {
    match rank {
        0 => Ok(Frame3MicroExpr::Zero),
        1 => Ok(Frame3MicroExpr::One),
        2 => Ok(Frame3MicroExpr::Nil),
        3 => Ok(Frame3MicroExpr::QuoteZero),
        4 => Ok(Frame3MicroExpr::QuoteOne),
        5 => Ok(Frame3MicroExpr::QuoteNil),
        _ => Err(Frame3MicroEnumerateError::RankOutOfRange),
    }
}

fn leaf_rank(expr: &Frame3MicroExpr) -> Option<u128> {
    match expr {
        Frame3MicroExpr::Zero => Some(0),
        Frame3MicroExpr::One => Some(1),
        Frame3MicroExpr::Nil => Some(2),
        Frame3MicroExpr::QuoteZero => Some(3),
        Frame3MicroExpr::QuoteOne => Some(4),
        Frame3MicroExpr::QuoteNil => Some(5),
        _ => None,
    }
}

fn unrank_exact(
    nodes: usize,
    mut rank: u128,
    counts: &[u128; COUNT_LIMIT + 1],
) -> Result<Frame3MicroExpr, Frame3MicroEnumerateError> {
    if nodes == 1 {
        return leaf_from_rank(rank);
    }
    if nodes > COUNT_LIMIT || rank >= counts[nodes] {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }

    let atom_block = counts[nodes - 1];
    if rank < atom_block {
        return Ok(Frame3MicroExpr::Atom(Box::new(unrank_exact(
            nodes - 1,
            rank,
            counts,
        )?)));
    }
    rank -= atom_block;

    for family in 0..3 {
        for left_nodes in 1..nodes - 1 {
            let right_nodes = nodes - 1 - left_nodes;
            let block = counts[left_nodes]
                .checked_mul(counts[right_nodes])
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
            if rank < block {
                let left_rank = rank / counts[right_nodes];
                let right_rank = rank % counts[right_nodes];
                let left = Box::new(unrank_exact(left_nodes, left_rank, counts)?);
                let right = Box::new(unrank_exact(right_nodes, right_rank, counts)?);
                return Ok(match family {
                    0 => Frame3MicroExpr::Cons(left, right),
                    1 => Frame3MicroExpr::CarCons(left, right),
                    _ => Frame3MicroExpr::CdrCons(left, right),
                });
            }
            rank -= block;
        }
    }

    for test_nodes in 1..nodes.saturating_sub(2) {
        for then_nodes in 1..nodes - 1 - test_nodes {
            let else_nodes = nodes - 1 - test_nodes - then_nodes;
            if else_nodes == 0 {
                continue;
            }
            let then_else = counts[then_nodes]
                .checked_mul(counts[else_nodes])
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
            let block = counts[test_nodes]
                .checked_mul(then_else)
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
            if rank < block {
                let test_rank = rank / then_else;
                let remainder = rank % then_else;
                let then_rank = remainder / counts[else_nodes];
                let else_rank = remainder % counts[else_nodes];
                return Ok(Frame3MicroExpr::IfAtom(
                    Box::new(unrank_exact(test_nodes, test_rank, counts)?),
                    Box::new(unrank_exact(then_nodes, then_rank, counts)?),
                    Box::new(unrank_exact(else_nodes, else_rank, counts)?),
                ));
            }
            rank -= block;
        }
    }

    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

fn rank_exact(
    expr: &Frame3MicroExpr,
    counts: &[u128; COUNT_LIMIT + 1],
) -> Result<u128, Frame3MicroEnumerateError> {
    let nodes = expr.node_count();
    if nodes == 1 {
        return leaf_rank(expr).ok_or(Frame3MicroEnumerateError::RankOutOfRange);
    }
    if nodes > COUNT_LIMIT {
        return Err(Frame3MicroEnumerateError::ProgramOutsideF3M4);
    }

    let atom_block = counts[nodes - 1];
    if let Frame3MicroExpr::Atom(value) = expr {
        return rank_exact(value, counts);
    }
    let mut rank = atom_block;

    let binary_pairs = (1..nodes - 1)
        .map(|left_nodes| {
            counts[left_nodes]
                .checked_mul(counts[nodes - 1 - left_nodes])
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)
        })
        .try_fold(0u128, |sum, value| {
            sum.checked_add(value?)
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)
        })?;

    let binary = match expr {
        Frame3MicroExpr::Cons(left, right) => Some((0u128, left, right)),
        Frame3MicroExpr::CarCons(left, right) => Some((1u128, left, right)),
        Frame3MicroExpr::CdrCons(left, right) => Some((2u128, left, right)),
        _ => None,
    };
    if let Some((family, left, right)) = binary {
        rank = rank
            .checked_add(
                family
                    .checked_mul(binary_pairs)
                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
            )
            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
        let left_nodes = left.node_count();
        let right_nodes = right.node_count();
        if left_nodes + right_nodes + 1 != nodes {
            return Err(Frame3MicroEnumerateError::RankOutOfRange);
        }
        for earlier_left in 1..left_nodes {
            let earlier_right = nodes - 1 - earlier_left;
            rank = rank
                .checked_add(
                    counts[earlier_left]
                        .checked_mul(counts[earlier_right])
                        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                )
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
        }
        rank = rank
            .checked_add(
                rank_exact(left, counts)?
                    .checked_mul(counts[right_nodes])
                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
            )
            .and_then(|value| value.checked_add(rank_exact(right, counts).ok()?))
            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
        return Ok(rank);
    }

    rank = rank
        .checked_add(
            binary_pairs
                .checked_mul(3)
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
        )
        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;

    if let Frame3MicroExpr::IfAtom(test, then_value, else_value) = expr {
        let test_nodes = test.node_count();
        let then_nodes = then_value.node_count();
        let else_nodes = else_value.node_count();
        if test_nodes + then_nodes + else_nodes + 1 != nodes {
            return Err(Frame3MicroEnumerateError::RankOutOfRange);
        }

        for earlier_test in 1..test_nodes {
            for earlier_then in 1..nodes - 1 - earlier_test {
                let earlier_else = nodes - 1 - earlier_test - earlier_then;
                if earlier_else == 0 {
                    continue;
                }
                rank = rank
                    .checked_add(
                        counts[earlier_test]
                            .checked_mul(counts[earlier_then])
                            .and_then(|value| value.checked_mul(counts[earlier_else]))
                            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                    )
                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
            }
        }
        for earlier_then in 1..then_nodes {
            let earlier_else = nodes - 1 - test_nodes - earlier_then;
            if earlier_else == 0 {
                continue;
            }
            rank = rank
                .checked_add(
                    counts[test_nodes]
                        .checked_mul(counts[earlier_then])
                        .and_then(|value| value.checked_mul(counts[earlier_else]))
                        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                )
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
        }

        let then_else = counts[then_nodes]
            .checked_mul(counts[else_nodes])
            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
        rank = rank
            .checked_add(
                rank_exact(test, counts)?
                    .checked_mul(then_else)
                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
            )
            .and_then(|value| {
                value.checked_add(
                    rank_exact(then_value, counts)
                        .ok()?
                        .checked_mul(counts[else_nodes])?,
                )
            })
            .and_then(|value| value.checked_add(rank_exact(else_value, counts).ok()?))
            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
        return Ok(rank);
    }

    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

fn update_minimum(slot: &mut Option<u128>, candidate: u128) {
    match slot {
        Some(current) if *current <= candidate => {}
        _ => *slot = Some(candidate),
    }
}

/// Small dynamic-programming proof over the 64 possible capability masks.
///
/// Returns the earliest global rank whose decoded program contains every bit
/// requested by `required`. This searches the grammar algebraically rather
/// than enumerating millions of physical payloads.
pub fn first_global_rank_with_capabilities(
    required: u8,
) -> Result<u128, Frame3MicroEnumerateError> {
    if required & !CAP_ALL != 0 {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }

    let counts = count_table()?;
    let mut minima = vec![[None::<u128>; 64]; COUNT_LIMIT + 1];
    // Node-one order: 0, 1, NIL, QUOTE(0), QUOTE(1), QUOTE(NIL).
    minima[1][0] = Some(0);
    minima[1][usize::from(CAP_QUOTE)] = Some(3);

    let mut cumulative = 0u128;
    for nodes in 1..=COUNT_LIMIT {
        if nodes > 1 {
            // ATOM is the first constructor block for an exact node count.
            for child_mask in 0..64 {
                if let Some(child_rank) = minima[nodes - 1][child_mask] {
                    let mask = child_mask | usize::from(CAP_ATOM);
                    update_minimum(&mut minima[nodes][mask], child_rank);
                }
            }

            let mut binary_pairs = 0u128;
            for left_nodes in 1..nodes - 1 {
                let right_nodes = nodes - 1 - left_nodes;
                binary_pairs = binary_pairs
                    .checked_add(
                        counts[left_nodes]
                            .checked_mul(counts[right_nodes])
                            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                    )
                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
            }

            let families = [CAP_CONS, CAP_CONS | CAP_CAR, CAP_CONS | CAP_CDR];
            for (family_index, family_mask) in families.into_iter().enumerate() {
                let mut split_offset = 0u128;
                for left_nodes in 1..nodes - 1 {
                    let right_nodes = nodes - 1 - left_nodes;
                    for left_mask in 0..64 {
                        let Some(left_rank) = minima[left_nodes][left_mask] else {
                            continue;
                        };
                        for right_mask in 0..64 {
                            let Some(right_rank) = minima[right_nodes][right_mask] else {
                                continue;
                            };
                            let rank = counts[nodes - 1]
                                .checked_add(
                                    (family_index as u128)
                                        .checked_mul(binary_pairs)
                                        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                                )
                                .and_then(|value| value.checked_add(split_offset))
                                .and_then(|value| {
                                    value.checked_add(left_rank.checked_mul(counts[right_nodes])?)
                                })
                                .and_then(|value| value.checked_add(right_rank))
                                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
                            let mask = usize::from(family_mask) | left_mask | right_mask;
                            update_minimum(&mut minima[nodes][mask], rank);
                        }
                    }
                    split_offset = split_offset
                        .checked_add(
                            counts[left_nodes]
                                .checked_mul(counts[right_nodes])
                                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                        )
                        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
                }
            }

            let if_base = counts[nodes - 1]
                .checked_add(
                    binary_pairs
                        .checked_mul(3)
                        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                )
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
            let mut split_offset = 0u128;
            for test_nodes in 1..nodes.saturating_sub(2) {
                for then_nodes in 1..nodes - 1 - test_nodes {
                    let else_nodes = nodes - 1 - test_nodes - then_nodes;
                    if else_nodes == 0 {
                        continue;
                    }
                    let then_else = counts[then_nodes]
                        .checked_mul(counts[else_nodes])
                        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
                    for test_mask in 0..64 {
                        let Some(test_rank) = minima[test_nodes][test_mask] else {
                            continue;
                        };
                        for then_mask in 0..64 {
                            let Some(then_rank) = minima[then_nodes][then_mask] else {
                                continue;
                            };
                            for else_mask in 0..64 {
                                let Some(else_rank) = minima[else_nodes][else_mask] else {
                                    continue;
                                };
                                let rank = if_base
                                    .checked_add(split_offset)
                                    .and_then(|value| {
                                        value.checked_add(test_rank.checked_mul(then_else)?)
                                    })
                                    .and_then(|value| {
                                        value
                                            .checked_add(then_rank.checked_mul(counts[else_nodes])?)
                                    })
                                    .and_then(|value| value.checked_add(else_rank))
                                    .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
                                let mask = usize::from(CAP_COND | CAP_ATOM)
                                    | test_mask
                                    | then_mask
                                    | else_mask;
                                update_minimum(&mut minima[nodes][mask], rank);
                            }
                        }
                    }
                    split_offset = split_offset
                        .checked_add(
                            counts[test_nodes]
                                .checked_mul(counts[then_nodes])
                                .and_then(|value| value.checked_mul(counts[else_nodes]))
                                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?,
                        )
                        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
                }
            }
        }

        let mut earliest = None;
        for (mask, rank) in minima[nodes].iter().enumerate() {
            if (mask as u8) & required == required {
                if let Some(rank) = rank {
                    update_minimum(&mut earliest, *rank);
                }
            }
        }
        if let Some(exact_rank) = earliest {
            let global = cumulative
                .checked_add(exact_rank)
                .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
            if global < F3M_END {
                return Ok(global);
            }
            return Err(Frame3MicroEnumerateError::ProgramOutsideF3M4);
        }

        cumulative = cumulative
            .checked_add(counts[nodes])
            .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
    }

    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

pub fn unrank_global(global_rank: u128) -> Result<Frame3MicroExpr, Frame3MicroEnumerateError> {
    if global_rank >= F3M_END {
        return Err(Frame3MicroEnumerateError::ProgramOutsideF3M4);
    }
    let counts = count_table()?;
    let mut remaining = global_rank;
    for nodes in 1..=COUNT_LIMIT {
        if remaining < counts[nodes] {
            return unrank_exact(nodes, remaining, &counts);
        }
        remaining -= counts[nodes];
    }
    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

pub fn rank_global(expr: &Frame3MicroExpr) -> Result<u128, Frame3MicroEnumerateError> {
    let counts = count_table()?;
    let nodes = expr.node_count();
    if nodes > COUNT_LIMIT {
        return Err(Frame3MicroEnumerateError::ProgramOutsideF3M4);
    }
    let rank = cumulative_before(nodes, &counts)?
        .checked_add(rank_exact(expr, &counts)?)
        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)?;
    if rank >= F3M_END {
        return Err(Frame3MicroEnumerateError::ProgramOutsideF3M4);
    }
    Ok(rank)
}

fn profile_offset(profile: Frame3MicroProfile) -> u128 {
    match profile {
        Frame3MicroProfile::F3M1 => 0,
        Frame3MicroProfile::F3M2 => F3M2_OFFSET,
        Frame3MicroProfile::F3M3 => F3M3_OFFSET,
        Frame3MicroProfile::F3M4 => F3M4_OFFSET,
        // Logical profile ordering only. F3M-5 uses its own prefix-stable
        // extension ranker rather than extending the legacy grammar order.
        Frame3MicroProfile::F3M5 => F3M_END,
    }
}

fn profile_capacity(profile: Frame3MicroProfile) -> u128 {
    match profile {
        Frame3MicroProfile::F3M1 => F3M1_CAPACITY,
        Frame3MicroProfile::F3M2 => F3M2_CAPACITY,
        Frame3MicroProfile::F3M3 => F3M3_CAPACITY,
        Frame3MicroProfile::F3M4 => F3M4_CAPACITY,
        Frame3MicroProfile::F3M5 => F3M5_CAPACITY,
    }
}

pub fn decode_payload(payload: &[u8]) -> Result<Frame3MicroExpr, Frame3MicroEnumerateError> {
    let profile = frame3_micro_profile(payload)
        .map_err(|error| Frame3MicroEnumerateError::UnsupportedLength(error.physical_bytes))?;
    let mut local = 0u128;
    for byte in payload {
        local = (local << 8) | u128::from(*byte);
    }
    if local >= profile_capacity(profile) {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }
    if profile == Frame3MicroProfile::F3M5 {
        return crate::frame3_micro_v5::decode_extension(local);
    }
    unrank_global(profile_offset(profile) + local)
}

pub fn encode_expr(expr: &Frame3MicroExpr) -> Result<Vec<u8>, Frame3MicroEnumerateError> {
    let (profile, local) = if crate::frame3_micro_v5::contains_extension(expr) {
        (
            Frame3MicroProfile::F3M5,
            crate::frame3_micro_v5::encode_extension(expr)?,
        )
    } else {
        let global = rank_global(expr)?;
        if global < F3M1_CAPACITY {
            (Frame3MicroProfile::F3M1, global)
        } else if global < F3M3_OFFSET {
            (Frame3MicroProfile::F3M2, global - F3M2_OFFSET)
        } else if global < F3M4_OFFSET {
            (Frame3MicroProfile::F3M3, global - F3M3_OFFSET)
        } else if global < F3M_END {
            (Frame3MicroProfile::F3M4, global - F3M4_OFFSET)
        } else {
            return Err(Frame3MicroEnumerateError::ProgramOutsideF3M4);
        }
    };

    let width = profile.physical_bytes();
    let mut payload = vec![0u8; width];
    let mut value = local;
    for byte in payload.iter_mut().rev() {
        *byte = value as u8;
        value >>= 8;
    }
    if value != 0 {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }
    Ok(payload)
}

pub const fn profile_program_capacity(profile: Frame3MicroProfile) -> u128 {
    match profile {
        Frame3MicroProfile::F3M1 => F3M1_CAPACITY,
        Frame3MicroProfile::F3M2 => F3M2_CAPACITY,
        Frame3MicroProfile::F3M3 => F3M3_CAPACITY,
        Frame3MicroProfile::F3M4 => F3M4_CAPACITY,
        Frame3MicroProfile::F3M5 => F3M5_CAPACITY,
    }
}

pub const fn profile_global_offset(profile: Frame3MicroProfile) -> u128 {
    match profile {
        Frame3MicroProfile::F3M1 => 0,
        Frame3MicroProfile::F3M2 => F3M2_OFFSET,
        Frame3MicroProfile::F3M3 => F3M3_OFFSET,
        Frame3MicroProfile::F3M4 => F3M4_OFFSET,
        Frame3MicroProfile::F3M5 => F3M_END,
    }
}

