#![cfg(all(target_os = "windows", target_arch = "x86_64"))]

// RED-then-GREEN witness for the Windows STATUS_HEAP_CORRUPTION finding
// recorded in knowledge/guard-reference-inbox.mylog
// (topic windows-virtualalloc-native-exec-heap-corruption).
//
// Hypothesis: the host called generated guest machine code through
// `extern "C"`, which on Windows x86-64 is the Win64 calling convention
// (arg1 in RCX). The Lisp-owned x86-64 guest ABI
// (lib/machine/lowering/semantic-x86-64.lisp) fixes arena pointer = RDI,
// result = RAX -- the SysV64 convention, which is what `extern "C"`
// happens to mean on Linux but not on Windows. Calling guest bytes that
// read their argument from RDI through a Win64-convention Rust function
// pointer reads whatever RDI held from the caller's own frame, not the
// arena pointer -- explaining why arena-free code (Jcc, plain ADD)
// worked while arena STORE/LOAD (CONS/CAR/CDR) eventually corrupted the
// heap.
//
// This test calls the trivial guest program `mov rax, rdi; ret`
// (bytes: 48 89 f8 c3) through both calling conventions and checks which
// one actually observes the pointer passed as the first argument.

type GuestIdentityWin64 = unsafe extern "system" fn(*mut u8) -> u64;
type GuestIdentitySysv64 = unsafe extern "sysv64" fn(*mut u8) -> u64;

// `mov rax, rdi; ret` -- reads the SysV64 first-argument register.
const MOV_RAX_RDI_RET: [u8; 4] = [0x48, 0x89, 0xf8, 0xc3];
// `mov rax, rcx; ret` -- reads the Win64 first-argument register. A
// positive pair test (this program through the Win64-convention pointer,
// MOV_RAX_RDI_RET through the SysV64-convention pointer) proves which
// register each convention actually delivers arg1 through, without
// assuming anything about what the "wrong" register happens to hold.
const MOV_RAX_RCX_RET: [u8; 4] = [0x48, 0x89, 0xc8, 0xc3];

mod raw_windows_exec {
    use std::ffi::c_void;

    #[link(name = "kernel32")]
    extern "system" {
        fn VirtualAlloc(
            address: *mut c_void,
            size: usize,
            allocation_type: u32,
            protect: u32,
        ) -> *mut c_void;
        fn VirtualProtect(
            address: *mut c_void,
            size: usize,
            new_protect: u32,
            old_protect: *mut u32,
        ) -> i32;
        fn VirtualFree(address: *mut c_void, size: usize, free_type: u32) -> i32;
        fn FlushInstructionCache(
            process: *mut c_void,
            address: *const c_void,
            size: usize,
        ) -> i32;
        fn GetCurrentProcess() -> *mut c_void;
    }

    const MEM_COMMIT: u32 = 0x1000;
    const MEM_RESERVE: u32 = 0x2000;
    const MEM_RELEASE: u32 = 0x8000;
    const PAGE_READWRITE: u32 = 0x04;
    const PAGE_EXECUTE_READ: u32 = 0x20;

    pub struct ExecutableGuestCode {
        pointer: *mut c_void,
        length: usize,
    }

    impl ExecutableGuestCode {
        pub fn install(bytes: &[u8]) -> Self {
            let length = bytes.len();
            let memory = unsafe {
                VirtualAlloc(
                    std::ptr::null_mut(),
                    length,
                    MEM_COMMIT | MEM_RESERVE,
                    PAGE_READWRITE,
                )
            };
            assert!(!memory.is_null(), "VirtualAlloc RW must succeed");

            unsafe {
                std::ptr::copy_nonoverlapping(bytes.as_ptr(), memory.cast::<u8>(), length);
            }

            let mut old_protect: u32 = 0;
            let protected = unsafe {
                VirtualProtect(memory, length, PAGE_EXECUTE_READ, &mut old_protect)
            };
            assert_ne!(protected, 0, "VirtualProtect RW->RX must succeed");

            let flushed = unsafe { FlushInstructionCache(GetCurrentProcess(), memory, length) };
            assert_ne!(flushed, 0, "FlushInstructionCache must succeed");

            ExecutableGuestCode {
                pointer: memory,
                length,
            }
        }

        pub fn as_ptr(&self) -> *mut c_void {
            self.pointer
        }
    }

    impl Drop for ExecutableGuestCode {
        fn drop(&mut self) {
            unsafe {
                VirtualFree(self.pointer, 0, MEM_RELEASE);
            }
            let _ = self.length;
        }
    }
}

#[test]
fn win64_calling_convention_delivers_the_arena_pointer_to_rcx_not_rdi() {
    let marker: u64 = 0xDEAD_BEEF_CAFE_F00D;

    // Positive proof: calling the RCX-reading program through the Win64
    // convention observes the marker...
    let rcx_reader = raw_windows_exec::ExecutableGuestCode::install(&MOV_RAX_RCX_RET);
    let function: GuestIdentityWin64 = unsafe { std::mem::transmute(rcx_reader.as_ptr()) };
    let observed_via_rcx = unsafe { function(marker as *mut u8) };
    assert_eq!(
        observed_via_rcx, marker,
        "extern \"system\" (Win64 ABI) must deliver arg1 via RCX on Windows x86-64"
    );

    // ...while calling the RDI-reading program through the same Win64
    // convention does not, without assuming anything about what RDI
    // happens to hold in that case.
    let rdi_reader = raw_windows_exec::ExecutableGuestCode::install(&MOV_RAX_RDI_RET);
    let function: GuestIdentityWin64 = unsafe { std::mem::transmute(rdi_reader.as_ptr()) };
    let observed_via_rdi = unsafe { function(marker as *mut u8) };
    assert_ne!(
        observed_via_rdi, marker,
        "extern \"system\" (Win64 ABI) must NOT deliver arg1 via RDI on Windows x86-64 -- \
         if this assertion fails, the ABI hypothesis is wrong and the real root cause is elsewhere"
    );
}

#[test]
fn sysv64_calling_convention_delivers_the_arena_pointer_to_rdi_not_rcx() {
    let marker: u64 = 0xDEAD_BEEF_CAFE_F00D;

    let rdi_reader = raw_windows_exec::ExecutableGuestCode::install(&MOV_RAX_RDI_RET);
    let function: GuestIdentitySysv64 = unsafe { std::mem::transmute(rdi_reader.as_ptr()) };
    let observed_via_rdi = unsafe { function(marker as *mut u8) };
    assert_eq!(
        observed_via_rdi, marker,
        "extern \"sysv64\" must deliver arg1 via RDI on Windows x86-64, matching the \
         Lisp-owned x86-64 guest ABI (arena pointer = RDI) -- this is the fix for the \
         STATUS_HEAP_CORRUPTION finding"
    );

    let rcx_reader = raw_windows_exec::ExecutableGuestCode::install(&MOV_RAX_RCX_RET);
    let function: GuestIdentitySysv64 = unsafe { std::mem::transmute(rcx_reader.as_ptr()) };
    let observed_via_rcx = unsafe { function(marker as *mut u8) };
    assert_ne!(
        observed_via_rcx, marker,
        "extern \"sysv64\" must NOT deliver arg1 via RCX on Windows x86-64 -- \
         if this assertion fails, the ABI hypothesis is wrong and the real root cause is elsewhere"
    );
}
