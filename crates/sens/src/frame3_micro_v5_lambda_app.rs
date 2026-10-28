//! Research-only F3M-5λA candidate: closed de Bruijn lambda terms with structural application in five bytes.
//!
//! This does not replace production F3M-5 or the already-proved F3M-5λ v1 candidate.
//! It explores a stronger grammar where one-argument LAMBDA has no textual parameter name
//! and APPLY(function, argument) is pure D2 call structure rather than a new domain resident.
//! Bound variables are de Bruijn references: BOUND(0) is the nearest binder.
//! Thus λx.x, λy.y, and λfoo.foo share one semantic identity: λ.BOUND(0).
//!
//! The candidate keeps the frozen F3M-1..4 grammar as state 0 and enumerates
//! only extension terms as state 1, so no 1..4-byte program is duplicated in
//! this 40-bit research space.

use crate::frame3_micro_enumerator::{
    Frame3MicroEnumerateError, CAP_ATOM, CAP_CAR, CAP_CDR, CAP_COND, CAP_CONS, CAP_EQ, CAP_LAMBDA,
    CAP_QUOTE,
};
use crate::{
    Bija3, Bit1, Bit3, Bit4, CoreD4, CoreDomainIdentity, DomainIdentity, ErrorKind, Expr, ExprKind,
    LanguageError, PredicateBit, Session, Span, Value,
};
use std::{rc::Rc, sync::OnceLock};

pub const F3M5_LAMBDA_CAPACITY: u128 = 1u128 << 40;
const MAX_NODES: usize = 13;
const MAX_DEPTH: usize = MAX_NODES + 1;
type Counts = [[[u128; 2]; MAX_DEPTH + 1]; MAX_NODES + 1];

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum F3m5LambdaExpr {
    Zero,
    One,
    Nil,
    QuoteZero,
    QuoteOne,
    QuoteNil,
    Bound(u8),
    Atom(Box<Self>),
    Cons(Box<Self>, Box<Self>),
    CarCons(Box<Self>, Box<Self>),
    CdrCons(Box<Self>, Box<Self>),
    EqAtom(Box<Self>, Box<Self>),
    Lambda(Box<Self>),
    /// Structural application: D2 list framing of function and one argument.
    Apply(Box<Self>, Box<Self>),
    IfAtom(Box<Self>, Box<Self>, Box<Self>),
}

#[derive(Clone, Debug, PartialEq)]
pub enum F3m5LambdaValue {
    Bit(bool),
    Nil,
    Pair(Box<Self>, Box<Self>),
    Closure {
        body: Box<F3m5LambdaExpr>,
        env: Vec<F3m5LambdaValue>,
    },
}

fn add(a: u128, b: u128) -> Result<u128, Frame3MicroEnumerateError> {
    a.checked_add(b)
        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)
}
fn mul(a: u128, b: u128) -> Result<u128, Frame3MicroEnumerateError> {
    a.checked_mul(b)
        .ok_or(Frame3MicroEnumerateError::InternalCountOverflow)
}
fn total(c: &Counts, n: usize, d: usize) -> Result<u128, Frame3MicroEnumerateError> {
    add(c[n][d][0], c[n][d][1])
}

fn build_counts() -> Result<Counts, Frame3MicroEnumerateError> {
    let mut c = [[[0u128; 2]; MAX_DEPTH + 1]; MAX_NODES + 1];
    for (d, row) in c[1].iter_mut().enumerate() {
        *row = [6, d as u128];
    }

    for n in 2..=MAX_NODES {
        for d in (0..MAX_DEPTH).rev() {
            let mut old = c[n - 1][d][0];

            let mut old_pairs = 0;
            for l in 1..n - 1 {
                let r = n - 1 - l;
                old_pairs = add(old_pairs, mul(c[l][d][0], c[r][d][0])?)?;
            }
            old = add(old, mul(3, old_pairs)?)?;

            for t in 1..n.saturating_sub(2) {
                for y in 1..n - 1 - t {
                    let z = n - 1 - t - y;
                    if z == 0 {
                        continue;
                    }
                    old = add(old, mul(mul(c[t][d][0], c[y][d][0])?, c[z][d][0])?)?;
                }
            }

            // ATOM(new child) + LAMBDA(any child one binder deeper).
            let mut new = add(c[n - 1][d][1], total(&c, n - 1, d + 1)?)?;

            // APPLY itself is new, so both children may be old or new.
            for l in 1..n - 1 {
                let r = n - 1 - l;
                let all = mul(total(&c, l, d)?, total(&c, r, d)?)?;
                new = add(new, all)?;
            }

            // CONS/CAR/CDR with >=1 new child, plus EQ with any children.
            for l in 1..n - 1 {
                let r = n - 1 - l;
                let all = mul(total(&c, l, d)?, total(&c, r, d)?)?;
                let old_pair = mul(c[l][d][0], c[r][d][0])?;
                new = add(new, mul(3, all - old_pair)?)?;
                new = add(new, all)?;
            }

            // IF-ATOM with >=1 new child.
            for t in 1..n.saturating_sub(2) {
                for y in 1..n - 1 - t {
                    let z = n - 1 - t - y;
                    if z == 0 {
                        continue;
                    }
                    let all = mul(mul(total(&c, t, d)?, total(&c, y, d)?)?, total(&c, z, d)?)?;
                    let old_triple = mul(mul(c[t][d][0], c[y][d][0])?, c[z][d][0])?;
                    new = add(new, all - old_triple)?;
                }
            }

            c[n][d] = [old, new];
        }
    }
    Ok(c)
}

fn counts() -> &'static Counts {
    static C: OnceLock<Counts> = OnceLock::new();
    C.get_or_init(|| build_counts().expect("bounded F3M-5λA counts fit u128"))
}

impl F3m5LambdaExpr {
    pub fn node_count(&self) -> usize {
        match self {
            Self::Zero
            | Self::One
            | Self::Nil
            | Self::QuoteZero
            | Self::QuoteOne
            | Self::QuoteNil
            | Self::Bound(_) => 1,
            Self::Atom(x) | Self::Lambda(x) => 1 + x.node_count(),
            Self::Cons(a, b)
            | Self::CarCons(a, b)
            | Self::CdrCons(a, b)
            | Self::EqAtom(a, b)
            | Self::Apply(a, b) => 1 + a.node_count() + b.node_count(),
            Self::IfAtom(a, b, c) => 1 + a.node_count() + b.node_count() + c.node_count(),
        }
    }

    pub fn contains_extension(&self) -> bool {
        match self {
            Self::Bound(_) | Self::Lambda(_) | Self::EqAtom(_, _) | Self::Apply(_, _) => true,
            Self::Atom(x) => x.contains_extension(),
            Self::Cons(a, b) | Self::CarCons(a, b) | Self::CdrCons(a, b) => {
                a.contains_extension() || b.contains_extension()
            }
            Self::IfAtom(a, b, c) => {
                a.contains_extension() || b.contains_extension() || c.contains_extension()
            }
            _ => false,
        }
    }

    pub fn capability_mask(&self) -> u8 {
        match self {
            Self::Zero | Self::One | Self::Nil | Self::Bound(_) => 0,
            Self::QuoteZero | Self::QuoteOne | Self::QuoteNil => CAP_QUOTE,
            Self::Atom(x) => CAP_ATOM | x.capability_mask(),
            Self::Cons(a, b) => CAP_CONS | a.capability_mask() | b.capability_mask(),
            Self::CarCons(a, b) => CAP_CAR | CAP_CONS | a.capability_mask() | b.capability_mask(),
            Self::CdrCons(a, b) => CAP_CDR | CAP_CONS | a.capability_mask() | b.capability_mask(),
            Self::EqAtom(a, b) => CAP_EQ | CAP_ATOM | a.capability_mask() | b.capability_mask(),
            Self::Lambda(x) => CAP_LAMBDA | x.capability_mask(),
            // APPLY is D2 structure, not a ninth semantic capability bit.
            Self::Apply(f, a) => f.capability_mask() | a.capability_mask(),
            Self::IfAtom(a, b, c) => {
                CAP_COND
                    | CAP_ATOM
                    | a.capability_mask()
                    | b.capability_mask()
                    | c.capability_mask()
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
            Self::Bound(i) => format!("BOUND({i})"),
            Self::Atom(x) => format!("ATOM({})", x.human_projection()),
            Self::Cons(a, b) => format!("CONS({},{})", a.human_projection(), b.human_projection()),
            Self::CarCons(a, b) => {
                format!(
                    "CAR(CONS({},{}))",
                    a.human_projection(),
                    b.human_projection()
                )
            }
            Self::CdrCons(a, b) => {
                format!(
                    "CDR(CONS({},{}))",
                    a.human_projection(),
                    b.human_projection()
                )
            }
            Self::EqAtom(a, b) => {
                format!(
                    "EQ(ATOM({}),ATOM({}))",
                    a.human_projection(),
                    b.human_projection()
                )
            }
            Self::Lambda(x) => format!("λ.{}", x.human_projection()),
            Self::Apply(f, a) => {
                format!("APPLY({},{})", f.human_projection(), a.human_projection())
            }
            Self::IfAtom(a, b, c) => format!(
                "IF-ATOM({},{},{})",
                a.human_projection(),
                b.human_projection(),
                c.human_projection()
            ),
        }
    }
}

fn old_leaf(rank: u128) -> Result<F3m5LambdaExpr, Frame3MicroEnumerateError> {
    match rank {
        0 => Ok(F3m5LambdaExpr::Zero),
        1 => Ok(F3m5LambdaExpr::One),
        2 => Ok(F3m5LambdaExpr::Nil),
        3 => Ok(F3m5LambdaExpr::QuoteZero),
        4 => Ok(F3m5LambdaExpr::QuoteOne),
        5 => Ok(F3m5LambdaExpr::QuoteNil),
        _ => Err(Frame3MicroEnumerateError::RankOutOfRange),
    }
}
fn old_leaf_rank(e: &F3m5LambdaExpr) -> Option<u128> {
    match e {
        F3m5LambdaExpr::Zero => Some(0),
        F3m5LambdaExpr::One => Some(1),
        F3m5LambdaExpr::Nil => Some(2),
        F3m5LambdaExpr::QuoteZero => Some(3),
        F3m5LambdaExpr::QuoteOne => Some(4),
        F3m5LambdaExpr::QuoteNil => Some(5),
        _ => None,
    }
}

fn unrank_old(
    n: usize,
    d: usize,
    mut rank: u128,
    c: &Counts,
) -> Result<F3m5LambdaExpr, Frame3MicroEnumerateError> {
    if n == 1 {
        return old_leaf(rank);
    }
    if rank >= c[n][d][0] {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }

    let block = c[n - 1][d][0];
    if rank < block {
        return Ok(F3m5LambdaExpr::Atom(Box::new(unrank_old(
            n - 1,
            d,
            rank,
            c,
        )?)));
    }
    rank -= block;

    for family in 0..3 {
        for l in 1..n - 1 {
            let r = n - 1 - l;
            let rc = c[r][d][0];
            let block = mul(c[l][d][0], rc)?;
            if rank < block {
                let a = Box::new(unrank_old(l, d, rank / rc, c)?);
                let b = Box::new(unrank_old(r, d, rank % rc, c)?);
                return Ok(match family {
                    0 => F3m5LambdaExpr::Cons(a, b),
                    1 => F3m5LambdaExpr::CarCons(a, b),
                    _ => F3m5LambdaExpr::CdrCons(a, b),
                });
            }
            rank -= block;
        }
    }

    for t in 1..n.saturating_sub(2) {
        for y in 1..n - 1 - t {
            let z = n - 1 - t - y;
            if z == 0 {
                continue;
            }
            let yz = mul(c[y][d][0], c[z][d][0])?;
            let block = mul(c[t][d][0], yz)?;
            if rank < block {
                let tr = rank / yz;
                let rem = rank % yz;
                return Ok(F3m5LambdaExpr::IfAtom(
                    Box::new(unrank_old(t, d, tr, c)?),
                    Box::new(unrank_old(y, d, rem / c[z][d][0], c)?),
                    Box::new(unrank_old(z, d, rem % c[z][d][0], c)?),
                ));
            }
            rank -= block;
        }
    }
    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

fn rank_old(e: &F3m5LambdaExpr, d: usize, c: &Counts) -> Result<u128, Frame3MicroEnumerateError> {
    if e.contains_extension() {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }
    let n = e.node_count();
    if n == 1 {
        return old_leaf_rank(e).ok_or(Frame3MicroEnumerateError::RankOutOfRange);
    }

    if let F3m5LambdaExpr::Atom(x) = e {
        return rank_old(x, d, c);
    }
    let mut rank = c[n - 1][d][0];

    let mut pairs = 0;
    for l in 1..n - 1 {
        pairs = add(pairs, mul(c[l][d][0], c[n - 1 - l][d][0])?)?;
    }

    let binary = match e {
        F3m5LambdaExpr::Cons(a, b) => Some((0u128, a, b)),
        F3m5LambdaExpr::CarCons(a, b) => Some((1u128, a, b)),
        F3m5LambdaExpr::CdrCons(a, b) => Some((2u128, a, b)),
        _ => None,
    };
    if let Some((family, a, b)) = binary {
        rank = add(rank, mul(family, pairs)?)?;
        let an = a.node_count();
        let bn = b.node_count();
        for l in 1..an {
            rank = add(rank, mul(c[l][d][0], c[n - 1 - l][d][0])?)?;
        }
        rank = add(rank, mul(rank_old(a, d, c)?, c[bn][d][0])?)?;
        return add(rank, rank_old(b, d, c)?);
    }

    rank = add(rank, mul(3, pairs)?)?;
    if let F3m5LambdaExpr::IfAtom(a, b, z) = e {
        let an = a.node_count();
        let bn = b.node_count();
        let zn = z.node_count();

        for t in 1..an {
            for y in 1..n - 1 - t {
                let zz = n - 1 - t - y;
                if zz > 0 {
                    rank = add(rank, mul(mul(c[t][d][0], c[y][d][0])?, c[zz][d][0])?)?;
                }
            }
        }
        for y in 1..bn {
            let zz = n - 1 - an - y;
            if zz > 0 {
                rank = add(rank, mul(mul(c[an][d][0], c[y][d][0])?, c[zz][d][0])?)?;
            }
        }

        let bz = mul(c[bn][d][0], c[zn][d][0])?;
        rank = add(rank, mul(rank_old(a, d, c)?, bz)?)?;
        rank = add(rank, mul(rank_old(b, d, c)?, c[zn][d][0])?)?;
        return add(rank, rank_old(z, d, c)?);
    }
    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

fn unrank_new(
    n: usize,
    d: usize,
    mut rank: u128,
    c: &Counts,
) -> Result<F3m5LambdaExpr, Frame3MicroEnumerateError> {
    if rank >= c[n][d][1] {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }
    if n == 1 {
        return (rank < d as u128)
            .then_some(F3m5LambdaExpr::Bound(rank as u8))
            .ok_or(Frame3MicroEnumerateError::RankOutOfRange);
    }

    let block = c[n - 1][d][1];
    if rank < block {
        return Ok(F3m5LambdaExpr::Atom(Box::new(unrank_new(
            n - 1,
            d,
            rank,
            c,
        )?)));
    }
    rank -= block;

    // New child first makes payload 0000000000 exactly λ.BOUND(0).
    for child_new in [true, false] {
        let block = c[n - 1][d + 1][usize::from(child_new)];
        if rank < block {
            let body = if child_new {
                unrank_new(n - 1, d + 1, rank, c)?
            } else {
                unrank_old(n - 1, d + 1, rank, c)?
            };
            return Ok(F3m5LambdaExpr::Lambda(Box::new(body)));
        }
        rank -= block;
    }

    for l in 1..n - 1 {
        let r = n - 1 - l;
        for (ln, rn) in [(false, false), (false, true), (true, false), (true, true)] {
            let rc = c[r][d][usize::from(rn)];
            let block = mul(c[l][d][usize::from(ln)], rc)?;
            if rank < block {
                let ar = rank / rc;
                let br = rank % rc;
                let function = if ln {
                    unrank_new(l, d, ar, c)?
                } else {
                    unrank_old(l, d, ar, c)?
                };
                let argument = if rn {
                    unrank_new(r, d, br, c)?
                } else {
                    unrank_old(r, d, br, c)?
                };
                return Ok(F3m5LambdaExpr::Apply(
                    Box::new(function),
                    Box::new(argument),
                ));
            }
            rank -= block;
        }
    }

    for family in 0..3 {
        for l in 1..n - 1 {
            let r = n - 1 - l;
            for (ln, rn) in [(false, true), (true, false), (true, true)] {
                let rc = c[r][d][usize::from(rn)];
                let block = mul(c[l][d][usize::from(ln)], rc)?;
                if rank < block {
                    let ar = rank / rc;
                    let br = rank % rc;
                    let a = if ln {
                        unrank_new(l, d, ar, c)?
                    } else {
                        unrank_old(l, d, ar, c)?
                    };
                    let b = if rn {
                        unrank_new(r, d, br, c)?
                    } else {
                        unrank_old(r, d, br, c)?
                    };
                    return Ok(match family {
                        0 => F3m5LambdaExpr::Cons(Box::new(a), Box::new(b)),
                        1 => F3m5LambdaExpr::CarCons(Box::new(a), Box::new(b)),
                        _ => F3m5LambdaExpr::CdrCons(Box::new(a), Box::new(b)),
                    });
                }
                rank -= block;
            }
        }
    }

    for l in 1..n - 1 {
        let r = n - 1 - l;
        for (ln, rn) in [(false, false), (false, true), (true, false), (true, true)] {
            let rc = c[r][d][usize::from(rn)];
            let block = mul(c[l][d][usize::from(ln)], rc)?;
            if rank < block {
                let ar = rank / rc;
                let br = rank % rc;
                let a = if ln {
                    unrank_new(l, d, ar, c)?
                } else {
                    unrank_old(l, d, ar, c)?
                };
                let b = if rn {
                    unrank_new(r, d, br, c)?
                } else {
                    unrank_old(r, d, br, c)?
                };
                return Ok(F3m5LambdaExpr::EqAtom(Box::new(a), Box::new(b)));
            }
            rank -= block;
        }
    }

    for t in 1..n.saturating_sub(2) {
        for y in 1..n - 1 - t {
            let z = n - 1 - t - y;
            if z == 0 {
                continue;
            }
            for mask in 1u8..=7 {
                let tn = mask & 4 != 0;
                let yn = mask & 2 != 0;
                let zn = mask & 1 != 0;
                let yc = c[y][d][usize::from(yn)];
                let zc = c[z][d][usize::from(zn)];
                let yz = mul(yc, zc)?;
                let block = mul(c[t][d][usize::from(tn)], yz)?;
                if rank < block {
                    let tr = rank / yz;
                    let rem = rank % yz;
                    let decode = |nodes, is_new, rr| {
                        if is_new {
                            unrank_new(nodes, d, rr, c)
                        } else {
                            unrank_old(nodes, d, rr, c)
                        }
                    };
                    return Ok(F3m5LambdaExpr::IfAtom(
                        Box::new(decode(t, tn, tr)?),
                        Box::new(decode(y, yn, rem / zc)?),
                        Box::new(decode(z, zn, rem % zc)?),
                    ));
                }
                rank -= block;
            }
        }
    }
    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

fn rank_new(e: &F3m5LambdaExpr, d: usize, c: &Counts) -> Result<u128, Frame3MicroEnumerateError> {
    if !e.contains_extension() {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }
    let n = e.node_count();
    if n == 1 {
        return match e {
            F3m5LambdaExpr::Bound(i) if usize::from(*i) < d => Ok(u128::from(*i)),
            _ => Err(Frame3MicroEnumerateError::RankOutOfRange),
        };
    }

    if let F3m5LambdaExpr::Atom(x) = e {
        if x.contains_extension() {
            return rank_new(x, d, c);
        }
    }
    let mut rank = c[n - 1][d][1];

    if let F3m5LambdaExpr::Lambda(body) = e {
        if body.contains_extension() {
            return add(rank, rank_new(body, d + 1, c)?);
        }
        rank = add(rank, c[n - 1][d + 1][1])?;
        return add(rank, rank_old(body, d + 1, c)?);
    }
    rank = add(rank, total(c, n - 1, d + 1)?)?;

    for l in 1..n - 1 {
        let r = n - 1 - l;
        for (ln, rn) in [(false, false), (false, true), (true, false), (true, true)] {
            let block = mul(c[l][d][usize::from(ln)], c[r][d][usize::from(rn)])?;
            if let F3m5LambdaExpr::Apply(function, argument) = e {
                if l == function.node_count()
                    && (ln, rn) == (function.contains_extension(), argument.contains_extension())
                {
                    let fr = if ln {
                        rank_new(function, d, c)?
                    } else {
                        rank_old(function, d, c)?
                    };
                    let ar = if rn {
                        rank_new(argument, d, c)?
                    } else {
                        rank_old(argument, d, c)?
                    };
                    rank = add(rank, mul(fr, c[r][d][usize::from(rn)])?)?;
                    return add(rank, ar);
                }
            }
            rank = add(rank, block)?;
        }
    }

    let binary = match e {
        F3m5LambdaExpr::Cons(a, b) => Some((0usize, a, b)),
        F3m5LambdaExpr::CarCons(a, b) => Some((1usize, a, b)),
        F3m5LambdaExpr::CdrCons(a, b) => Some((2usize, a, b)),
        _ => None,
    };
    for family in 0..3 {
        for l in 1..n - 1 {
            let r = n - 1 - l;
            for (ln, rn) in [(false, true), (true, false), (true, true)] {
                let block = mul(c[l][d][usize::from(ln)], c[r][d][usize::from(rn)])?;
                if let Some((actual_family, a, b)) = binary {
                    if family == actual_family
                        && l == a.node_count()
                        && (ln, rn) == (a.contains_extension(), b.contains_extension())
                    {
                        let ar = if ln {
                            rank_new(a, d, c)?
                        } else {
                            rank_old(a, d, c)?
                        };
                        let br = if rn {
                            rank_new(b, d, c)?
                        } else {
                            rank_old(b, d, c)?
                        };
                        rank = add(rank, mul(ar, c[r][d][usize::from(rn)])?)?;
                        return add(rank, br);
                    }
                }
                rank = add(rank, block)?;
            }
        }
    }

    for l in 1..n - 1 {
        let r = n - 1 - l;
        for (ln, rn) in [(false, false), (false, true), (true, false), (true, true)] {
            let block = mul(c[l][d][usize::from(ln)], c[r][d][usize::from(rn)])?;
            if let F3m5LambdaExpr::EqAtom(a, b) = e {
                if l == a.node_count()
                    && (ln, rn) == (a.contains_extension(), b.contains_extension())
                {
                    let ar = if ln {
                        rank_new(a, d, c)?
                    } else {
                        rank_old(a, d, c)?
                    };
                    let br = if rn {
                        rank_new(b, d, c)?
                    } else {
                        rank_old(b, d, c)?
                    };
                    rank = add(rank, mul(ar, c[r][d][usize::from(rn)])?)?;
                    return add(rank, br);
                }
            }
            rank = add(rank, block)?;
        }
    }

    if let F3m5LambdaExpr::IfAtom(a, b, z) = e {
        let actual_nodes = (a.node_count(), b.node_count(), z.node_count());
        let actual_mask = (u8::from(a.contains_extension()) << 2)
            | (u8::from(b.contains_extension()) << 1)
            | u8::from(z.contains_extension());
        for t in 1..n.saturating_sub(2) {
            for y in 1..n - 1 - t {
                let zz = n - 1 - t - y;
                if zz == 0 {
                    continue;
                }
                for mask in 1u8..=7 {
                    let tn = mask & 4 != 0;
                    let yn = mask & 2 != 0;
                    let zn = mask & 1 != 0;
                    let block = mul(
                        mul(c[t][d][usize::from(tn)], c[y][d][usize::from(yn)])?,
                        c[zz][d][usize::from(zn)],
                    )?;
                    if (t, y, zz) == actual_nodes && mask == actual_mask {
                        let rr = |x: &F3m5LambdaExpr, is_new| {
                            if is_new {
                                rank_new(x, d, c)
                            } else {
                                rank_old(x, d, c)
                            }
                        };
                        let yz = mul(c[y][d][usize::from(yn)], c[zz][d][usize::from(zn)])?;
                        rank = add(rank, mul(rr(a, tn)?, yz)?)?;
                        rank = add(rank, mul(rr(b, yn)?, c[zz][d][usize::from(zn)])?)?;
                        return add(rank, rr(z, zn)?);
                    }
                    rank = add(rank, block)?;
                }
            }
        }
    }
    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

pub fn decode_candidate(payload: [u8; 5]) -> Result<F3m5LambdaExpr, Frame3MicroEnumerateError> {
    let mut rank = 0u128;
    for b in payload {
        rank = (rank << 8) | u128::from(b);
    }
    let c = counts();
    let mut remaining = rank;
    for n in 1..=MAX_NODES {
        let block = c[n][0][1];
        if remaining < block {
            return unrank_new(n, 0, remaining, c);
        }
        remaining -= block;
    }
    Err(Frame3MicroEnumerateError::RankOutOfRange)
}

pub fn encode_candidate(e: &F3m5LambdaExpr) -> Result<[u8; 5], Frame3MicroEnumerateError> {
    if !e.contains_extension() || e.node_count() > MAX_NODES {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }
    let c = counts();
    let mut rank = 0;
    // Work directly on the rank table: no indexed walk, extra bit-width,
    // or accidental overflow/truncation before emitting five bytes.
    for row in c.iter().take(e.node_count()).skip(1) {
        rank = add(rank, row[0][1])?;
    }
    rank = add(rank, rank_new(e, 0, c)?)?;
    if rank >= F3M5_LAMBDA_CAPACITY {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    }

    let mut out = [0u8; 5];
    for b in out.iter_mut().rev() {
        *b = rank as u8;
        rank >>= 8;
    }
    Ok(out)
}

fn atom(v: &F3m5LambdaValue) -> bool {
    !matches!(v, F3m5LambdaValue::Pair(_, _))
}

fn eval_env(
    e: &F3m5LambdaExpr,
    env: &[F3m5LambdaValue],
) -> Result<F3m5LambdaValue, Frame3MicroEnumerateError> {
    match e {
        F3m5LambdaExpr::Zero | F3m5LambdaExpr::QuoteZero => Ok(F3m5LambdaValue::Bit(false)),
        F3m5LambdaExpr::One | F3m5LambdaExpr::QuoteOne => Ok(F3m5LambdaValue::Bit(true)),
        F3m5LambdaExpr::Nil | F3m5LambdaExpr::QuoteNil => Ok(F3m5LambdaValue::Nil),
        F3m5LambdaExpr::Bound(i) => env
            .get(usize::from(*i))
            .cloned()
            .ok_or(Frame3MicroEnumerateError::RankOutOfRange),
        F3m5LambdaExpr::Atom(x) => Ok(F3m5LambdaValue::Bit(atom(&eval_env(x, env)?))),
        F3m5LambdaExpr::Cons(a, b) => Ok(F3m5LambdaValue::Pair(
            Box::new(eval_env(a, env)?),
            Box::new(eval_env(b, env)?),
        )),
        F3m5LambdaExpr::CarCons(a, b) => {
            let a = eval_env(a, env)?;
            let _ = eval_env(b, env)?;
            Ok(a)
        }
        F3m5LambdaExpr::CdrCons(a, b) => {
            let _ = eval_env(a, env)?;
            eval_env(b, env)
        }
        F3m5LambdaExpr::EqAtom(a, b) => Ok(F3m5LambdaValue::Bit(
            atom(&eval_env(a, env)?) == atom(&eval_env(b, env)?),
        )),
        F3m5LambdaExpr::Lambda(body) => Ok(F3m5LambdaValue::Closure {
            body: body.clone(),
            env: env.to_vec(),
        }),
        F3m5LambdaExpr::Apply(function, argument) => {
            let function = eval_env(function, env)?;
            let argument = eval_env(argument, env)?;
            apply_candidate(function, argument)
        }
        F3m5LambdaExpr::IfAtom(test, yes, no) => {
            if atom(&eval_env(test, env)?) {
                eval_env(yes, env)
            } else {
                eval_env(no, env)
            }
        }
    }
}

pub fn eval_candidate(e: &F3m5LambdaExpr) -> Result<F3m5LambdaValue, Frame3MicroEnumerateError> {
    eval_env(e, &[])
}

pub fn apply_candidate(
    closure: F3m5LambdaValue,
    arg: F3m5LambdaValue,
) -> Result<F3m5LambdaValue, Frame3MicroEnumerateError> {
    let F3m5LambdaValue::Closure { body, env } = closure else {
        return Err(Frame3MicroEnumerateError::RankOutOfRange);
    };
    let mut bound = Vec::with_capacity(env.len() + 1);
    bound.push(arg);
    bound.extend(env);
    eval_env(&body, &bound)
}

/// Internal evaluator-only binder token used solely to allocate one call-frame
/// slot for a nameless lambda.  F3M-5λ semantic identity never contains this
/// string: every bound occurrence is already an ExprKind::Local coordinate.
///
/// A NUL prefix keeps this token outside ordinary parsed source spellings.  If
/// this debug/arity token changes, the physical five-byte mapping and lowered
/// Local coordinates remain identical.
const RUNTIME_BINDER_SENTINEL: &str = "\0f3m-debruijn-slot";

fn runtime_expr(kind: ExprKind) -> Expr {
    Expr {
        kind,
        span: Span::default(),
    }
}

fn runtime_list(items: Vec<Expr>) -> Expr {
    runtime_expr(ExprKind::List(Rc::from(items.into_boxed_slice())))
}

fn runtime_d1(bit: bool) -> Expr {
    runtime_expr(ExprKind::DomainIdentity(DomainIdentity::D1(
        PredicateBit::from_word(Bit1::new(u8::from(bit)).expect("D1 bit")),
    )))
}

fn runtime_d3(bits: u8, arguments: Vec<Expr>) -> Expr {
    runtime_expr(ExprKind::DomainCall(
        CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(bits).expect("D3 word"))),
        Rc::from(arguments.into_boxed_slice()),
    ))
}

fn runtime_lambda(body: Expr) -> Expr {
    let parameter = runtime_expr(ExprKind::Symbol(Rc::from(RUNTIME_BINDER_SENTINEL)));
    let parameters = runtime_list(vec![parameter]);
    runtime_expr(ExprKind::DomainCall(
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0010).expect("D4 LAMBDA"))),
        Rc::from(vec![parameters, body].into_boxed_slice()),
    ))
}

fn lower_runtime(expression: &F3m5LambdaExpr, lexical_depth: usize) -> Result<Expr, LanguageError> {
    Ok(match expression {
        F3m5LambdaExpr::Zero => runtime_d1(false),
        F3m5LambdaExpr::One => runtime_d1(true),
        F3m5LambdaExpr::Nil => runtime_list(vec![]),
        F3m5LambdaExpr::QuoteZero => runtime_d3(0b001, vec![runtime_d1(false)]),
        F3m5LambdaExpr::QuoteOne => runtime_d3(0b001, vec![runtime_d1(true)]),
        F3m5LambdaExpr::QuoteNil => runtime_d3(0b001, vec![runtime_list(vec![])]),
        F3m5LambdaExpr::Bound(index) => {
            if usize::from(*index) >= lexical_depth {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("F3M-5λA BOUND({index}) is free at lexical depth {lexical_depth}"),
                    Span::default(),
                ));
            }
            runtime_expr(ExprKind::Local {
                depth: u32::from(*index),
                index: 0,
            })
        }
        F3m5LambdaExpr::Atom(value) => {
            runtime_d3(0b010, vec![lower_runtime(value, lexical_depth)?])
        }
        F3m5LambdaExpr::Cons(left, right) => runtime_d3(
            0b111,
            vec![
                lower_runtime(left, lexical_depth)?,
                lower_runtime(right, lexical_depth)?,
            ],
        ),
        F3m5LambdaExpr::CarCons(left, right) => {
            let cons = runtime_d3(
                0b111,
                vec![
                    lower_runtime(left, lexical_depth)?,
                    lower_runtime(right, lexical_depth)?,
                ],
            );
            runtime_d3(0b100, vec![cons])
        }
        F3m5LambdaExpr::CdrCons(left, right) => {
            let cons = runtime_d3(
                0b111,
                vec![
                    lower_runtime(left, lexical_depth)?,
                    lower_runtime(right, lexical_depth)?,
                ],
            );
            runtime_d3(0b011, vec![cons])
        }
        F3m5LambdaExpr::EqAtom(left, right) => {
            let left = runtime_d3(0b010, vec![lower_runtime(left, lexical_depth)?]);
            let right = runtime_d3(0b010, vec![lower_runtime(right, lexical_depth)?]);
            runtime_d3(0b101, vec![left, right])
        }
        F3m5LambdaExpr::Lambda(body) => runtime_lambda(lower_runtime(body, lexical_depth + 1)?),
        F3m5LambdaExpr::Apply(function, argument) => runtime_list(vec![
            lower_runtime(function, lexical_depth)?,
            lower_runtime(argument, lexical_depth)?,
        ]),
        F3m5LambdaExpr::IfAtom(test, yes, no) => {
            let predicate = runtime_d3(0b010, vec![lower_runtime(test, lexical_depth)?]);
            let yes_clause = runtime_list(vec![predicate, lower_runtime(yes, lexical_depth)?]);
            let no_clause = runtime_list(vec![runtime_d1(true), lower_runtime(no, lexical_depth)?]);
            runtime_d3(0b110, vec![yes_clause, no_clause])
        }
    })
}

/// Lower the nameless five-byte candidate directly into SENS's existing
/// numeric lexical-slot AST.  Bound-variable names never enter the result:
/// BOUND(n) becomes Local { depth: n, index: 0 }.
///
/// The only temporary string is the evaluator-private lambda-list sentinel
/// required by the current Closure arity/frame allocator.  It is never
/// referenced by the body and therefore cannot affect semantic identity.
pub fn lower_candidate_to_sens_expr(expression: &F3m5LambdaExpr) -> Result<Expr, LanguageError> {
    lower_runtime(expression, 0)
}

/// Evaluate a decoded F3M-5λ term with the real SENS evaluator, not the small
/// research evaluator above.
pub fn eval_candidate_with_sens_runtime(
    expression: &F3m5LambdaExpr,
    session: &mut Session,
) -> Result<Value, LanguageError> {
    let lowered = lower_candidate_to_sens_expr(expression)?;
    crate::eval_expr(&lowered, &session.environment)
}

/// Decode an exact five-byte F3M-5λ payload and run it through the real SENS
/// evaluator.  Decode errors remain distinct from language-evaluation errors.
pub fn decode_and_eval_with_sens_runtime(
    payload: [u8; 5],
    session: &mut Session,
) -> Result<Value, String> {
    let expression = decode_candidate(payload).map_err(|error| format!("{error}"))?;
    eval_candidate_with_sens_runtime(&expression, session).map_err(|error| error.to_string())
}

