// Host-specific executable-memory adapter for native_exec.rs. The guest
// calling convention (extern "sysv64", arena pointer = RDI, result = RAX)
// is the same Lisp-owned ABI on every platform; only how we obtain RWX
// memory from the OS differs here.

use std::ffi::c_void;

pub(crate) struct ExecutableMemory {
    pointer: *mut c_void,
    length: usize,
}

impl ExecutableMemory {
    pub(crate) fn as_ptr(&self) -> *mut c_void {
        self.pointer
    }
}

#[cfg(all(unix, target_arch = "x86_64"))]
mod imp {
    use super::ExecutableMemory;
    use std::ffi::c_void;

    const PROT_READ: i32 = 0x1;
    const PROT_WRITE: i32 = 0x2;
    const PROT_EXEC: i32 = 0x4;
    const MAP_PRIVATE: i32 = 0x02;
    const MAP_ANONYMOUS: i32 = 0x20;

    extern "C" {
        fn mmap(
            address: *mut c_void,
            length: usize,
            protection: i32,
            flags: i32,
            file_descriptor: i32,
            offset: isize,
        ) -> *mut c_void;
        fn mprotect(address: *mut c_void, length: usize, protection: i32) -> i32;
        fn munmap(address: *mut c_void, length: usize) -> i32;
    }

    pub(crate) fn allocate_rw(length: usize) -> Result<ExecutableMemory, String> {
        let memory = unsafe {
            mmap(
                std::ptr::null_mut(),
                length,
                PROT_READ | PROT_WRITE,
                MAP_PRIVATE | MAP_ANONYMOUS,
                -1,
                0,
            )
        };
        if memory as isize == -1 {
            return Err(format!("mmap RW failed: {}", std::io::Error::last_os_error()));
        }
        Ok(ExecutableMemory {
            pointer: memory,
            length,
        })
    }

    pub(crate) fn make_executable(memory: &ExecutableMemory) -> Result<(), String> {
        if unsafe { mprotect(memory.pointer, memory.length, PROT_READ | PROT_EXEC) } != 0 {
            return Err(format!(
                "mprotect RW->RX failed: {}",
                std::io::Error::last_os_error()
            ));
        }
        Ok(())
    }

    pub(crate) fn release(memory: &ExecutableMemory) -> Result<(), String> {
        if unsafe { munmap(memory.pointer, memory.length) } != 0 {
            return Err(format!("munmap failed: {}", std::io::Error::last_os_error()));
        }
        Ok(())
    }
}

#[cfg(all(windows, target_arch = "x86_64"))]
mod imp {
    use super::ExecutableMemory;
    use std::ffi::c_void;

    const MEM_COMMIT: u32 = 0x1000;
    const MEM_RESERVE: u32 = 0x2000;
    const MEM_RELEASE: u32 = 0x8000;
    const PAGE_READWRITE: u32 = 0x04;
    const PAGE_EXECUTE_READ: u32 = 0x20;

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

    pub(crate) fn allocate_rw(length: usize) -> Result<ExecutableMemory, String> {
        let memory = unsafe {
            VirtualAlloc(
                std::ptr::null_mut(),
                length,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_READWRITE,
            )
        };
        if memory.is_null() {
            return Err(format!(
                "VirtualAlloc RW failed: {}",
                std::io::Error::last_os_error()
            ));
        }
        Ok(ExecutableMemory {
            pointer: memory,
            length,
        })
    }

    pub(crate) fn make_executable(memory: &ExecutableMemory) -> Result<(), String> {
        let mut old_protect: u32 = 0;
        let protected = unsafe {
            VirtualProtect(
                memory.pointer,
                memory.length,
                PAGE_EXECUTE_READ,
                &mut old_protect,
            )
        };
        if protected == 0 {
            return Err(format!(
                "VirtualProtect RW->RX failed: {}",
                std::io::Error::last_os_error()
            ));
        }
        let flushed = unsafe {
            FlushInstructionCache(GetCurrentProcess(), memory.pointer, memory.length)
        };
        if flushed == 0 {
            return Err(format!(
                "FlushInstructionCache failed: {}",
                std::io::Error::last_os_error()
            ));
        }
        Ok(())
    }

    pub(crate) fn release(memory: &ExecutableMemory) -> Result<(), String> {
        // dwSize must be exactly 0 for MEM_RELEASE, per Microsoft's
        // VirtualFree documentation.
        let freed = unsafe { VirtualFree(memory.pointer, 0, MEM_RELEASE) };
        if freed == 0 {
            return Err(format!(
                "VirtualFree failed: {}",
                std::io::Error::last_os_error()
            ));
        }
        Ok(())
    }
}

pub(crate) use imp::{allocate_rw, make_executable, release};
