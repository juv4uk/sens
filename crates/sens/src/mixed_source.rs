//! Mixed human/source parser bridge for the exact-domain migration.
//!
//! The ordinary Lisp parser remains unchanged. This bridge is intentionally
//! bounded to executable list heads:
//! - exact 3/4/5/6-bit binary heads become DomainIdentity;
//! - exact 7-bit heads fail closed because current D7 is
//!   Sound/Text/local-ordinal, not callable;
//! - exact 8-bit heads remain the ordinary parser's compatibility path;
//!   this bridge does not infer current D8;
//! - non-head data keeps the ordinary parser's interpretation.
//!
//! This gives active Core migration a mixed symbol + exact-domain path without
//! teaching the compatibility parser to infer domains from historical bytes.

use crate::syntax::{Expr, ExprKind, MAX_STRUCTURE_DEPTH};
use crate::{parse_binary_source_words, DomainIdentity, ErrorKind, LanguageError};
use std::rc::Rc;
