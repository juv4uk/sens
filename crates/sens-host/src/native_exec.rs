use sens::{Environment, ErrorKind, Exactness, LanguageError, Span, Value};

const MAX_EXACT_LISP_INTEGER: u64 = 9_007_199_254_740_991;
const MAX_NATIVE_ARENA_BYTES: usize = 1_048_576;

// The Lisp-owned x86-64 guest ABI (lib/machine/lowering/semantic-x86-64.lisp)
// fixes arena pointer = RDI, result = RAX -- the SysV64 convention. On Linux
// `extern "C"` happens to mean SysV64, so the two coincided by accident. On
// Windows `extern "C"` means the Win64 convention (arg1 = RCX), which does
// NOT match the guest ABI. Keep one explicit SysV64 guest boundary on every
// host OS, but isolate arbitrary admitted guest register writes from the Rust
// caller: guest code is not required to preserve host nonvolatile registers.
//
// This trampoline is host mechanism only. It neither decodes guest bytes nor
// owns any Lisp/machine semantic fact. The Lisp-owned machine layer still
// chooses forms/encoding; this adapter only preserves the calling frame while
// entering and leaving those bytes.
#[unsafe(naked)]
unsafe extern "sysv64" fn call_guest_preserving_sysv64_nonvolatile(
    _entry: *const u8,
    _arena: *mut u8,
) -> u64 {
    core::arch::naked_asm!(
        // Wrapper SysV64 args: RDI = guest entry, RSI = arena pointer.
        "mov r11, rdi",
        // Guest ABI: RDI = arena pointer (null for the no-arena shape).
        "mov rdi, rsi",
        // Arbitrary admitted guest code may write every GPR. Preserve the
        // registers that this SysV64 wrapper owes to its Rust caller.
        "push rbx",
        "push rbp",
        "push r12",
        "push r13",
        "push r14",
        "push r15",
        // Six pushes leave RSP == 8 (mod 16). Align before CALL so the guest
        // sees the standard SysV64 entry alignment RSP == 8 (mod 16).
        "sub rsp, 8",
        "call r11",
        "add rsp, 8",
        // RAX is deliberately untouched: it is the Lisp-owned guest result.
        "pop r15",
        "pop r14",
        "pop r13",
        "pop r12",
        "pop rbp",
        "pop rbx",
        "ret",
    );
}

use crate::platform::{self, ExecutableMemory};

fn mechanism_error(operation: &str, action: &str, detail: &str, span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::InvalidForm,
        format!("{operation}: {action} failed: {detail}"),
        span,
    )
}

fn expect_machine_bytes(
    value: &Value,
    operation: &str,
    span: Span,
) -> Result<Vec<u8>, LanguageError> {
    let mut bytes = Vec::new();
    let mut current = value;

    loop {
        match current {
            Value::Nil => return Ok(bytes),
            Value::Pair(head, tail) => {
                let Value::Number(number, Exactness::Exact) = **head else {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        format!("{operation} expects exact byte integers 0-255"),
                        span,
                    ));
                };
                if number.fract() != 0.0 || !(0.0..=255.0).contains(&number) {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        format!("{operation} expects exact byte integers 0-255"),
                        span,
                    ));
                }
                bytes.push(number as u8);
                current = tail;
            }
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    format!("{operation} expects a proper list of exact byte integers 0-255"),
                    span,
                ));
            }
        }
    }
}

fn expect_arena_length(value: &Value, span: Span) -> Result<usize, LanguageError> {
    let Value::Number(number, Exactness::Exact) = value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "native-call-u64-raw expects an exact positive arena byte count",
            span,
        ));
    };
    if number.fract() != 0.0 || *number < 1.0 || *number > MAX_NATIVE_ARENA_BYTES as f64 {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!("native-call-u64-raw arena byte count must be 1..={MAX_NATIVE_ARENA_BYTES}"),
            span,
        ));
    }
    Ok(*number as usize)
}

fn prepare_executable(
    bytes: &[u8],
    operation: &str,
    span: Span,
) -> Result<ExecutableMemory, LanguageError> {
    if bytes.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!("{operation} refuses an empty machine-code buffer"),
            span,
        ));
    }

    let memory = platform::allocate_rw(bytes.len())
        .map_err(|detail| mechanism_error(operation, "allocate RW", &detail, span))?;

    unsafe {
        std::ptr::copy_nonoverlapping(bytes.as_ptr(), memory.as_ptr().cast::<u8>(), bytes.len());
    }

    if let Err(detail) = platform::make_executable(&memory) {
        let _ = platform::release(&memory);
        return Err(mechanism_error(operation, "make executable", &detail, span));
    }

    Ok(memory)
}

fn execute_u64(bytes: &[u8], span: Span) -> Result<u64, LanguageError> {
    let operation = "native-call-u64-raw";
    let memory = prepare_executable(bytes, operation, span)?;
    let result = unsafe {
        call_guest_preserving_sysv64_nonvolatile(memory.as_ptr().cast::<u8>(), std::ptr::null_mut())
    };

    platform::release(&memory)
        .map_err(|detail| mechanism_error(operation, "release code", &detail, span))?;

    Ok(result)
}

fn execute_u64_with_arena(
    bytes: &[u8],
    arena_length: usize,
    span: Span,
) -> Result<u64, LanguageError> {
    let operation = "native-call-u64-raw";
    let code = prepare_executable(bytes, operation, span)?;
    let arena = platform::allocate_rw(arena_length).map_err(|detail| {
        let _ = platform::release(&code);
        mechanism_error(operation, "allocate arena", &detail, span)
    })?;

    let result = unsafe {
        call_guest_preserving_sysv64_nonvolatile(
            code.as_ptr().cast::<u8>(),
            arena.as_ptr().cast::<u8>(),
        )
    };

    let code_release = platform::release(&code);
    let arena_release = platform::release(&arena);
    if let Err(detail) = code_release {
        return Err(mechanism_error(operation, "release code", &detail, span));
    }
    if let Err(detail) = arena_release {
        return Err(mechanism_error(operation, "release arena", &detail, span));
    }

    Ok(result)
}

fn result_value(result: u64, operation: &str, span: Span) -> Result<Value, LanguageError> {
    if result > MAX_EXACT_LISP_INTEGER {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!("{operation} result exceeds sens's exact integer range"),
            span,
        ));
    }

    Ok(Value::Number(result as f64, Exactness::Exact))
}

pub(crate) fn evaluate_native_call_u64_raw(
    arguments: &[Value],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let operation = "native-call-u64-raw";
    if !(1..=2).contains(&arguments.len()) {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            format!(
                "{operation}: expected 1 or 2 arguments; received {}",
                arguments.len()
            ),
            span,
        ));
    }

    let bytes = expect_machine_bytes(&arguments[0], operation, span)?;
    let result = if arguments.len() == 1 {
        execute_u64(&bytes, span)?
    } else {
        let arena_length = expect_arena_length(&arguments[1], span)?;
        execute_u64_with_arena(&bytes, arena_length, span)?
    };
    result_value(result, operation, span)
}
