"""Minimal executable WebAssembly controls for #3681.

The modules are deliberately tiny mechanism controls with no Rust/C toolchain baggage.
They expose one function `run() -> i32`; i32 zero is mapped to SENS structural empty
for the two D3 smoke fixtures.
"""

from __future__ import annotations


def uleb(value: int) -> bytes:
    if value < 0:
        raise ValueError("ULEB requires a non-negative integer")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def section(section_id: int, payload: bytes) -> bytes:
    return bytes([section_id]) + uleb(len(payload)) + payload


MAGIC_VERSION = b"\x00asm\x01\x00\x00\x00"
TYPE_RUN_I32 = bytes([1, 0x60, 0, 1, 0x7F])
FUNCTION_ONE_TYPE0 = bytes([1, 0])
EXPORT_RUN_FUNC0 = bytes([1, 3]) + b"run" + bytes([0, 0])


def quote_empty_module() -> bytes:
    # (func (export "run") (result i32) (i32.const 0))
    body = bytes([0, 0x41, 0, 0x0B])
    code = bytes([1]) + uleb(len(body)) + body
    return b"".join(
        (
            MAGIC_VERSION,
            section(1, TYPE_RUN_I32),
            section(3, FUNCTION_ONE_TYPE0),
            section(7, EXPORT_RUN_FUNC0),
            section(10, code),
        )
    )


def car_empty_module() -> bytes:
    # One page of memory. At address 0 store an 8-byte pair [head=0, tail=0].
    # run() loads the head i32 at address 0.
    memory = bytes([1, 0, 1])  # vec=1, min-only limits, min=1 page
    body = bytes([0, 0x41, 0, 0x28, 0x02, 0, 0x0B])  # i32.load align=4 offset=0
    code = bytes([1]) + uleb(len(body)) + body
    data = bytes([1, 0, 0x41, 0, 0x0B, 8]) + bytes(8)
    return b"".join(
        (
            MAGIC_VERSION,
            section(1, TYPE_RUN_I32),
            section(3, FUNCTION_ONE_TYPE0),
            section(5, memory),
            section(7, EXPORT_RUN_FUNC0),
            section(10, code),
            section(11, data),
        )
    )


MODULES = {
    "d3-quote-empty": quote_empty_module,
    "d3-car-empty": car_empty_module,
}
