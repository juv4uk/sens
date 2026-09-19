use crate::value::{Rational, Value};
use crate::Exactness;
use std::rc::Rc;

// IEEE 754 NaN boxing masks

const MASK_QNAN: u64 = 0x7FF0_0000_0000_0000; // All exponent bits 1

// fpga-lisp tags (lower 32 bits, bits 28..31 are tag)
pub const TAG_FIXNUM: u64 = 0;
pub const TAG_CONS: u64 = 1;
pub const TAG_SYMBOL: u64 = 2;
pub const TAG_NIL: u64 = 3;
pub const TAG_TRUE: u64 = 4;
pub const TAG_PRIMITIVE: u64 = 5;
pub const TAG_STRING: u64 = 6;
pub const TAG_RATIONAL: u64 = 7;
pub const TAG_CLOSURE: u64 = 8;
pub const TAG_MACRO: u64 = 9;
pub const TAG_TCP_CONN: u64 = 10;
pub const TAG_TCP_LIST: u64 = 11;
pub const TAG_NUMERIC_BUFFER: u64 = 13;
/// Host-only implementation projection. Unlike TAG_PRIMITIVE this payload is
/// an address and therefore is not portable semantic identity.
pub const TAG_HOST_BUILTIN: u64 = 14;
pub const TAG_HOST_HANDLE: u64 = 15;

#[derive(Debug, Copy, Clone)]
pub struct NanBox(pub u64);

impl NanBox {
    /// Pack a 48-bit pointer and a 4-bit tag into a 64-bit NaN-boxed value.
    /// The pointer is split: lower 28 bits in `bits 0..27`, upper 20 bits in `bits 32..51`.
    /// The tag is placed in `bits 28..31`, perfectly matching fpga-lisp's 32-bit ISA layout.
    fn pack_ptr(tag: u64, ptr: u64) -> u64 {
        let ptr_low = ptr & 0x0FFF_FFFF;
        let ptr_high = (ptr >> 28) & 0x000F_FFFF;
        MASK_QNAN | (ptr_high << 32) | (tag << 28) | ptr_low
    }

    pub fn from_value(value: &Value) -> Self {
        match value {
            Value::Nil => NanBox(MASK_QNAN | (TAG_NIL << 28)),
            Value::Bool(true) => NanBox(MASK_QNAN | (TAG_TRUE << 28)),
            Value::Bool(false) => NanBox(MASK_QNAN | (TAG_NIL << 28)), // false is nil in fpga-lisp
            Value::Number(f, Exactness::Inexact) => NanBox(f.to_bits()),
            Value::Number(f, Exactness::Exact) => {
                let i = *f as i32;
                let payload = (i as u32) & 0x0FFF_FFFF;
                NanBox(MASK_QNAN | (TAG_FIXNUM << 28) | (payload as u64))
            }
            Value::Rational(r) => {
                let ptr = r as *const Rational as u64;
                NanBox(Self::pack_ptr(TAG_RATIONAL, ptr))
            }
            Value::String(s) => {
                let ptr = Rc::as_ptr(s) as *const u8 as u64;
                NanBox(Self::pack_ptr(TAG_STRING, ptr))
            }
            Value::Symbol(s) => {
                let ptr = Rc::as_ptr(s) as *const u8 as u64;
                NanBox(Self::pack_ptr(TAG_SYMBOL, ptr))
            }
            Value::Pair(h, _t) => {
                // Since my-lisp uses Rc for Pair but fpga-lisp expects a cons cell pointer.
                // We'll pack the Pair object pointer.
                // Note: This is an unowned reference encoding (Memory Layout Boundary only).
                let ptr = h as *const Rc<Value> as u64;
                NanBox(Self::pack_ptr(TAG_CONS, ptr))
            }
            Value::Closure(c) => {
                let ptr = Rc::as_ptr(c) as u64;
                NanBox(Self::pack_ptr(TAG_CLOSURE, ptr))
            }
            Value::Macro(m) => {
                let ptr = Rc::as_ptr(m) as u64;
                NanBox(Self::pack_ptr(TAG_MACRO, ptr))
            }
            // Portable primitive identity is the numeric semantic ID itself,
            // not an address of whichever host implementation happens to run it.
            Value::SemanticRef(semantic_id) => {
                NanBox(MASK_QNAN | (TAG_PRIMITIVE << 28) | u64::from(*semantic_id))
            }
            // Legacy non-Canon host builtins remain representable, but their
            // address is explicitly tagged as host mechanism, never primitive identity.
            Value::Builtin(b) => {
                let ptr = Rc::as_ptr(b) as u64;
                NanBox(Self::pack_ptr(TAG_HOST_BUILTIN, ptr))
            }
            Value::HostHandle { token, .. } => {
                NanBox(MASK_QNAN | (TAG_HOST_HANDLE << 28) | (token & 0x0FFF_FFFF))
            }
            Value::Vector(v) => {
                let ptr = Rc::as_ptr(v) as *const u8 as u64;
                NanBox(Self::pack_ptr(12, ptr))
            }
            Value::NumericBuffer(crate::NumericBuffer::I32(values)) => {
                NanBox(Self::pack_ptr(TAG_NUMERIC_BUFFER, values.as_ptr() as u64))
            }
            Value::NumericBuffer(crate::NumericBuffer::F32(values)) => {
                NanBox(Self::pack_ptr(TAG_NUMERIC_BUFFER, values.as_ptr() as u64))
            }
            Value::TcpConnection(c) => {
                let ptr = Rc::as_ptr(c) as u64;
                NanBox(Self::pack_ptr(TAG_TCP_CONN, ptr))
            }
            Value::TcpListener(l) => {
                let ptr = Rc::as_ptr(l) as u64;
                NanBox(Self::pack_ptr(TAG_TCP_LIST, ptr))
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn semantic_ref_nanbox_payload_is_the_numeric_identity() {
        let NanBox(bits) = NanBox::from_value(&Value::SemanticRef(5));
        assert_eq!((bits >> 28) & 0xF, TAG_PRIMITIVE);
        assert_eq!(bits & 0x0FFF_FFFF, 5);
    }
}
