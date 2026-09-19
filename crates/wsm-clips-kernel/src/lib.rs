//! Native CLIPS island boundary.
//!
//! This crate owns only mechanical access to the external CLIPS C runtime.
//! It does not reimplement CLIPS semantics and does not assign meaning to
//! my-lisp semantic IDs.
//!
//! The default build is runtime-independent. With the `native-clips` feature
//! enabled, CLIPS is loaded dynamically at runtime rather than linked into the
//! my-lisp binary. Set `WSM_CLIPS_LIBRARY` to an exact shared-library path,
//! or let the platform loader try a conventional CLIPS library name.

use std::ffi::c_void;
use std::fmt;

use wsm_kernel_c_abi::{
    WsmKernelKind, WsmKernelRequest, WsmKernelVTable, WsmMutableByteSpan, WsmStatus,
    WSM_KERNEL_ABI_VERSION,
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClipsKernelError {
    NativeFeatureDisabled,
    #[cfg(feature = "native-clips")]
    LibraryLoad(String),
    #[cfg(feature = "native-clips")]
    MissingSymbol(String),
    #[cfg(feature = "native-clips")]
    CreateEnvironmentFailed,
    #[cfg(feature = "native-clips")]
    NulInput,
    #[cfg(feature = "native-clips")]
    BuildFailed(u32),
    #[cfg(feature = "native-clips")]
    AssertFailed,
    #[cfg(feature = "native-clips")]
    RetractFailed(u32),
}

impl fmt::Display for ClipsKernelError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NativeFeatureDisabled => write!(
                f,
                "native CLIPS support is not enabled; rebuild with feature native-clips"
            ),
            #[cfg(feature = "native-clips")]
            Self::LibraryLoad(message) => write!(f, "unable to load CLIPS runtime: {message}"),
            #[cfg(feature = "native-clips")]
            Self::MissingSymbol(message) => write!(f, "CLIPS runtime is missing a required symbol: {message}"),
            #[cfg(feature = "native-clips")]
            Self::CreateEnvironmentFailed => write!(f, "CLIPS CreateEnvironment returned null"),
            #[cfg(feature = "native-clips")]
            Self::NulInput => write!(f, "CLIPS input contains an interior NUL byte"),
            #[cfg(feature = "native-clips")]
            Self::BuildFailed(code) => write!(f, "CLIPS Build failed with error code {code}"),
            #[cfg(feature = "native-clips")]
            Self::AssertFailed => write!(f, "CLIPS AssertString returned null"),
            #[cfg(feature = "native-clips")]
            Self::RetractFailed(code) => write!(f, "CLIPS Retract failed with error code {code}"),
        }
    }
}

impl std::error::Error for ClipsKernelError {}

#[cfg(not(feature = "native-clips"))]
#[derive(Debug, Default)]
pub struct ClipsKernel;

#[cfg(not(feature = "native-clips"))]
impl ClipsKernel {
    pub const fn native_feature_enabled() -> bool {
        false
    }

    pub fn create_environment(&self) -> Result<(), ClipsKernelError> {
        Err(ClipsKernelError::NativeFeatureDisabled)
    }
}

#[cfg(feature = "native-clips")]
mod native {
    use super::ClipsKernelError;
    use std::ffi::{c_char, c_longlong, c_ulong, c_void, CStr, CString, OsStr};
    use std::rc::Rc;

    #[repr(C)]
    pub struct Environment {
        _private: [u8; 0],
    }

    #[repr(C)]
    pub struct Fact {
        _private: [u8; 0],
    }

    type CreateEnvironmentFn = unsafe extern "C" fn() -> *mut Environment;
    type DestroyEnvironmentFn = unsafe extern "C" fn(*mut Environment) -> bool;
    type BuildFn = unsafe extern "C" fn(*mut Environment, *const c_char) -> u32;
    type AssertStringFn = unsafe extern "C" fn(*mut Environment, *const c_char) -> *mut Fact;
    type RunFn = unsafe extern "C" fn(*mut Environment, c_longlong) -> c_longlong;
    type RetractFn = unsafe extern "C" fn(*mut Fact) -> u32;
    type GetNumberOfFactsFn = unsafe extern "C" fn(*mut Environment) -> c_ulong;
    type RetainFactFn = unsafe extern "C" fn(*mut Fact);
    type ReleaseFactFn = unsafe extern "C" fn(*mut Fact);

    #[cfg(unix)]
    mod loader {
        use super::*;

        const RTLD_NOW: i32 = 2;
        const RTLD_GLOBAL: i32 = 0x100;

        #[cfg_attr(not(target_os = "macos"), link(name = "dl"))]
        unsafe extern "C" {
            fn dlopen(filename: *const c_char, flags: i32) -> *mut c_void;
            fn dlsym(handle: *mut c_void, symbol: *const c_char) -> *mut c_void;
            fn dlclose(handle: *mut c_void) -> i32;
            fn dlerror() -> *const c_char;
        }

        pub struct DynamicLibrary {
            dependencies: Vec<*mut c_void>,
            handle: *mut c_void,
        }

        impl DynamicLibrary {
            pub unsafe fn open(path: &OsStr) -> Result<Self, String> {
                use std::os::unix::ffi::OsStrExt;

                let mut dependencies = Vec::new();

                #[cfg(all(target_os = "linux", target_env = "gnu"))]
                {
                    let libm = CString::new("libm.so.6").expect("static libm name has no NUL");
                    let math_handle = unsafe { dlopen(libm.as_ptr(), RTLD_NOW | RTLD_GLOBAL) };
                    if math_handle.is_null() {
                        return Err(format!("unable to preload libm.so.6: {}", last_error()));
                    }
                    dependencies.push(math_handle);
                }

                let path = CString::new(path.as_bytes())
                    .map_err(|_| "library path contains an interior NUL byte".to_string())?;
                let handle = unsafe { dlopen(path.as_ptr(), RTLD_NOW) };
                if handle.is_null() {
                    for dependency in dependencies.drain(..).rev() {
                        let _ = unsafe { dlclose(dependency) };
                    }
                    return Err(last_error());
                }
                Ok(Self {
                    dependencies,
                    handle,
                })
            }

            pub unsafe fn symbol<T: Copy>(&self, name: &'static [u8]) -> Result<T, String> {
                let symbol_name = CStr::from_bytes_with_nul(name)
                    .map_err(|_| "symbol name is not NUL-terminated".to_string())?;
                let ptr = unsafe { dlsym(self.handle, symbol_name.as_ptr()) };
                if ptr.is_null() {
                    return Err(last_error());
                }
                if std::mem::size_of::<T>() != std::mem::size_of::<*mut c_void>() {
                    return Err("function pointer size does not match dynamic symbol pointer".to_string());
                }
                Ok(unsafe { std::mem::transmute_copy::<*mut c_void, T>(&ptr) })
            }
        }

        impl Drop for DynamicLibrary {
            fn drop(&mut self) {
                if !self.handle.is_null() {
                    let _ = unsafe { dlclose(self.handle) };
                    self.handle = std::ptr::null_mut();
                }
                for dependency in self.dependencies.drain(..).rev() {
                    let _ = unsafe { dlclose(dependency) };
                }
            }
        }

        fn last_error() -> String {
            let ptr = unsafe { dlerror() };
            if ptr.is_null() {
                "dynamic loader returned no error text".to_string()
            } else {
                unsafe { CStr::from_ptr(ptr) }.to_string_lossy().into_owned()
            }
        }
    }

    #[cfg(windows)]
    mod loader {
        use super::*;

        #[link(name = "kernel32")]
        unsafe extern "system" {
            fn LoadLibraryW(name: *const u16) -> *mut c_void;
            fn GetProcAddress(module: *mut c_void, name: *const u8) -> *mut c_void;
            fn FreeLibrary(module: *mut c_void) -> i32;
            fn GetLastError() -> u32;
        }

        pub struct DynamicLibrary {
            handle: *mut c_void,
        }

        impl DynamicLibrary {
            pub unsafe fn open(path: &OsStr) -> Result<Self, String> {
                use std::os::windows::ffi::OsStrExt;
                let mut wide: Vec<u16> = path.encode_wide().collect();
                wide.push(0);
                let handle = unsafe { LoadLibraryW(wide.as_ptr()) };
                if handle.is_null() {
                    return Err(format!("LoadLibraryW failed with code {}", unsafe { GetLastError() }));
                }
                Ok(Self { handle })
            }

            pub unsafe fn symbol<T: Copy>(&self, name: &'static [u8]) -> Result<T, String> {
                let ptr = unsafe { GetProcAddress(self.handle, name.as_ptr()) };
                if ptr.is_null() {
                    return Err(format!("GetProcAddress failed with code {}", unsafe { GetLastError() }));
                }
                if std::mem::size_of::<T>() != std::mem::size_of::<*mut c_void>() {
                    return Err("function pointer size does not match dynamic symbol pointer".to_string());
                }
                Ok(unsafe { std::mem::transmute_copy::<*mut c_void, T>(&ptr) })
            }
        }

        impl Drop for DynamicLibrary {
            fn drop(&mut self) {
                if !self.handle.is_null() {
                    let _ = unsafe { FreeLibrary(self.handle) };
                    self.handle = std::ptr::null_mut();
                }
            }
        }
    }

    use loader::DynamicLibrary;

    pub struct NativeApi {
        _library: DynamicLibrary,
        pub create_environment: CreateEnvironmentFn,
        pub destroy_environment: DestroyEnvironmentFn,
        pub build: BuildFn,
        pub assert_string: AssertStringFn,
        pub run: RunFn,
        pub retract: RetractFn,
        pub get_number_of_facts: GetNumberOfFactsFn,
        pub retain_fact: RetainFactFn,
        pub release_fact: ReleaseFactFn,
    }

    impl NativeApi {
        pub unsafe fn load(path: impl AsRef<OsStr>) -> Result<Rc<Self>, ClipsKernelError> {
            let library = unsafe { DynamicLibrary::open(path.as_ref()) }
                .map_err(ClipsKernelError::LibraryLoad)?;

            unsafe fn load_symbol<T: Copy>(
                library: &DynamicLibrary,
                name: &'static [u8],
            ) -> Result<T, ClipsKernelError> {
                unsafe { library.symbol::<T>(name) }.map_err(|error| {
                    let printable = String::from_utf8_lossy(name)
                        .trim_end_matches('\0')
                        .to_string();
                    ClipsKernelError::MissingSymbol(format!("{printable}: {error}"))
                })
            }

            let create_environment = unsafe { load_symbol(&library, b"CreateEnvironment\0")? };
            let destroy_environment = unsafe { load_symbol(&library, b"DestroyEnvironment\0")? };
            let build = unsafe { load_symbol(&library, b"Build\0")? };
            let assert_string = unsafe { load_symbol(&library, b"AssertString\0")? };
            let run = unsafe { load_symbol(&library, b"Run\0")? };
            let retract = unsafe { load_symbol(&library, b"Retract\0")? };
            let get_number_of_facts = unsafe { load_symbol(&library, b"GetNumberOfFacts\0")? };
            let retain_fact = unsafe { load_symbol(&library, b"RetainFact\0")? };
            let release_fact = unsafe { load_symbol(&library, b"ReleaseFact\0")? };

            Ok(Rc::new(Self {
                _library: library,
                create_environment,
                destroy_environment,
                build,
                assert_string,
                run,
                retract,
                get_number_of_facts,
                retain_fact,
                release_fact,
            }))
        }
    }

    pub fn candidate_library_names() -> &'static [&'static str] {
        #[cfg(target_os = "windows")]
        {
            &["clips.dll", "libclips.dll"]
        }
        #[cfg(target_os = "macos")]
        {
            &["libclips.dylib", "clips.dylib"]
        }
        #[cfg(all(unix, not(target_os = "macos")))]
        {
            &["libclips.so", "clips.so"]
        }
        #[cfg(not(any(target_os = "windows", target_os = "macos", unix)))]
        {
            &[]
        }
    }
}

#[cfg(feature = "native-clips")]
pub struct ClipsKernel {
    api: std::rc::Rc<native::NativeApi>,
}

#[cfg(feature = "native-clips")]
impl ClipsKernel {
    pub const fn native_feature_enabled() -> bool {
        true
    }

    pub fn load(path: impl AsRef<std::ffi::OsStr>) -> Result<Self, ClipsKernelError> {
        let api = unsafe { native::NativeApi::load(path)? };
        Ok(Self { api })
    }

    pub fn discover() -> Result<Self, ClipsKernelError> {
        if let Some(path) = std::env::var_os("WSM_CLIPS_LIBRARY") {
            return Self::load(path);
        }

        let mut failures = Vec::new();
        for candidate in native::candidate_library_names() {
            match Self::load(candidate) {
                Ok(kernel) => return Ok(kernel),
                Err(error) => failures.push(format!("{candidate}: {error}")),
            }
        }

        Err(ClipsKernelError::LibraryLoad(if failures.is_empty() {
            "no platform CLIPS library candidates are defined; set WSM_CLIPS_LIBRARY".to_string()
        } else {
            format!(
                "{}; set WSM_CLIPS_LIBRARY to the exact shared-library path",
                failures.join("; ")
            )
        }))
    }

    pub fn create_environment(&self) -> Result<ClipsEnvironment, ClipsKernelError> {
        let raw = unsafe { (self.api.create_environment)() };
        if raw.is_null() {
            return Err(ClipsKernelError::CreateEnvironmentFailed);
        }
        Ok(ClipsEnvironment {
            inner: std::rc::Rc::new(EnvironmentInner {
                api: self.api.clone(),
                raw,
            }),
        })
    }
}

#[cfg(feature = "native-clips")]
struct EnvironmentInner {
    api: std::rc::Rc<native::NativeApi>,
    raw: *mut native::Environment,
}

#[cfg(feature = "native-clips")]
pub struct ClipsEnvironment {
    inner: std::rc::Rc<EnvironmentInner>,
}

#[cfg(feature = "native-clips")]
impl ClipsEnvironment {
    pub fn build(&self, construct: &str) -> Result<(), ClipsKernelError> {
        let construct =
            std::ffi::CString::new(construct).map_err(|_| ClipsKernelError::NulInput)?;
        let code = unsafe { (self.inner.api.build)(self.inner.raw, construct.as_ptr()) };
        if code == 0 {
            Ok(())
        } else {
            Err(ClipsKernelError::BuildFailed(code))
        }
    }

    pub fn assert_string(&self, fact: &str) -> Result<ClipsFact, ClipsKernelError> {
        let fact = std::ffi::CString::new(fact).map_err(|_| ClipsKernelError::NulInput)?;
        let raw = unsafe { (self.inner.api.assert_string)(self.inner.raw, fact.as_ptr()) };
        if raw.is_null() {
            Err(ClipsKernelError::AssertFailed)
        } else {
            unsafe { (self.inner.api.retain_fact)(raw) };
            Ok(ClipsFact {
                environment: self.inner.clone(),
                raw,
                retained: true,
            })
        }
    }

    pub fn run(&self, limit: i64) -> i64 {
        unsafe { (self.inner.api.run)(self.inner.raw, limit) }
    }

    pub fn fact_count(&self) -> u64 {
        u64::from(unsafe { (self.inner.api.get_number_of_facts)(self.inner.raw) })
    }

    pub fn retract(&self, mut fact: ClipsFact) -> Result<(), ClipsKernelError> {
        let raw = fact.raw;
        if fact.retained {
            unsafe { (self.inner.api.release_fact)(raw) };
            fact.retained = false;
        }
        let code = unsafe { (self.inner.api.retract)(raw) };
        if code == 0 {
            Ok(())
        } else {
            Err(ClipsKernelError::RetractFailed(code))
        }
    }
}

#[cfg(feature = "native-clips")]
impl Drop for EnvironmentInner {
    fn drop(&mut self) {
        if !self.raw.is_null() {
            let _ = unsafe { (self.api.destroy_environment)(self.raw) };
            self.raw = std::ptr::null_mut();
        }
    }
}

#[cfg(feature = "native-clips")]
pub struct ClipsFact {
    environment: std::rc::Rc<EnvironmentInner>,
    raw: *mut native::Fact,
    retained: bool,
}

#[cfg(feature = "native-clips")]
impl Drop for ClipsFact {
    fn drop(&mut self) {
        if self.retained && !self.raw.is_null() {
            unsafe {
                (self.environment.api.release_fact)(self.raw)
            };
            self.retained = false;
        }
    }
}

/// Opaque my-lisp semantic identity. The CLIPS adapter preserves this byte as
/// provenance and never maps it to CLIPS constructs, facts, rules or agenda
/// operations.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SemanticId(pub u8);

struct ClipsAbiContext {
    rule: String,
    fact_text: String,
    running: bool,
    last_semantic_id: Option<SemanticId>,
    last_fired: Option<i64>,
    #[cfg(feature = "native-clips")]
    environment: Option<ClipsEnvironment>,
    #[cfg(feature = "native-clips")]
    fact: Option<ClipsFact>,
}

/// Mechanical adapter from the shared C ABI to one native CLIPS environment.
///
/// The payload is a kernel-local transport command (run or retract). The
/// semantic ID is not interpreted by this crate.
pub struct ClipsAbiAdapter {
    context: Box<ClipsAbiContext>,
    vtable: WsmKernelVTable,
}

impl ClipsAbiAdapter {
    pub fn new(rule: impl Into<String>, fact: impl Into<String>) -> Self {
        let mut context = Box::new(ClipsAbiContext {
            rule: rule.into(),
            fact_text: fact.into(),
            running: false,
            last_semantic_id: None,
            last_fired: None,
            #[cfg(feature = "native-clips")]
            environment: None,
            #[cfg(feature = "native-clips")]
            fact: None,
        });
        let context_ptr = (&mut *context) as *mut ClipsAbiContext as *mut c_void;
        let vtable = WsmKernelVTable {
            abi_version: WSM_KERNEL_ABI_VERSION,
            kernel: WsmKernelKind::Clips,
            context: context_ptr,
            start: Some(clips_start),
            exchange: Some(clips_exchange),
            snapshot: Some(clips_snapshot),
            stop: Some(clips_stop),
        };
        Self { context, vtable }
    }

    pub fn vtable(&self) -> WsmKernelVTable {
        self.vtable
    }

    pub fn last_semantic_id(&self) -> Option<SemanticId> {
        self.context.last_semantic_id
    }

    pub fn last_fired(&self) -> Option<i64> {
        self.context.last_fired
    }
}

unsafe fn clips_context_mut<'a>(context: *mut c_void) -> Option<&'a mut ClipsAbiContext> {
    unsafe { (context as *mut ClipsAbiContext).as_mut() }
}

unsafe extern "C" fn clips_start(context: *mut c_void) -> WsmStatus {
    let Some(context) = (unsafe { clips_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };

    #[cfg(not(feature = "native-clips"))]
    {
        let _ = context;
        return WsmStatus::KernelFailure;
    }

    #[cfg(feature = "native-clips")]
    {
        let kernel = match ClipsKernel::discover() {
            Ok(kernel) => kernel,
            Err(_) => return WsmStatus::KernelFailure,
        };
        let environment = match kernel.create_environment() {
            Ok(environment) => environment,
            Err(_) => return WsmStatus::KernelFailure,
        };
        if environment.build(&context.rule).is_err() {
            return WsmStatus::KernelFailure;
        }
        let fact = match environment.assert_string(&context.fact_text) {
            Ok(fact) => fact,
            Err(_) => return WsmStatus::KernelFailure,
        };
        context.environment = Some(environment);
        context.fact = Some(fact);
        context.running = true;
        WsmStatus::Ok
    }
}

unsafe extern "C" fn clips_stop(context: *mut c_void) -> WsmStatus {
    let Some(context) = (unsafe { clips_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };
    #[cfg(feature = "native-clips")]
    {
        context.fact = None;
        context.environment = None;
    }
    context.running = false;
    WsmStatus::Ok
}

fn copy_response(bytes: &[u8], response: WsmMutableByteSpan, written: *mut usize) -> WsmStatus {
    if written.is_null() {
        return WsmStatus::InvalidArgument;
    }
    unsafe { *written = 0; }
    if response.len < bytes.len() {
        unsafe { *written = bytes.len(); }
        return WsmStatus::BufferTooSmall;
    }
    if !bytes.is_empty() && response.ptr.is_null() {
        return WsmStatus::InvalidArgument;
    }
    if !bytes.is_empty() {
        unsafe {
            std::ptr::copy_nonoverlapping(bytes.as_ptr(), response.ptr, bytes.len());
        }
    }
    unsafe { *written = bytes.len(); }
    WsmStatus::Ok
}

unsafe extern "C" fn clips_exchange(
    context: *mut c_void,
    request: WsmKernelRequest,
    response: WsmMutableByteSpan,
    written: *mut usize,
) -> WsmStatus {
    if written.is_null() {
        return WsmStatus::InvalidArgument;
    }
    unsafe { *written = 0; }

    let Some(context) = (unsafe { clips_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };
    if !context.running {
        return WsmStatus::NotRunning;
    }
    if request.payload.len != 0 && request.payload.ptr.is_null() {
        return WsmStatus::InvalidArgument;
    }
    let payload = if request.payload.len == 0 {
        &[]
    } else {
        unsafe { std::slice::from_raw_parts(request.payload.ptr, request.payload.len) }
    };
    let Ok(command) = std::str::from_utf8(payload) else {
        return WsmStatus::InvalidArgument;
    };

    #[cfg(not(feature = "native-clips"))]
    {
        let _ = (command, response);
        return WsmStatus::KernelFailure;
    }

    #[cfg(feature = "native-clips")]
    {
        let Some(environment) = context.environment.as_mut() else {
            return WsmStatus::NotRunning;
        };
        let output = match command {
            "run" => {
                let fired = environment.run(-1);
                context.last_fired = Some(fired);
                format!("fired={fired}\n").into_bytes()
            }
            "retract" => {
                let Some(fact) = context.fact.take() else {
                    return WsmStatus::KernelFailure;
                };
                if environment.retract(fact).is_err() {
                    return WsmStatus::KernelFailure;
                }
                b"retracted\n".to_vec()
            }
            _ => return WsmStatus::InvalidArgument,
        };
        context.last_semantic_id = Some(SemanticId(request.semantic_id));
        copy_response(&output, response, written)
    }
}

unsafe extern "C" fn clips_snapshot(
    context: *mut c_void,
    response: WsmMutableByteSpan,
    written: *mut usize,
) -> WsmStatus {
    let Some(context) = (unsafe { clips_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };
    let bytes = match context.last_fired {
        Some(value) => format!("last-fired={value}\n").into_bytes(),
        None => Vec::new(),
    };
    copy_response(&bytes, response, written)
}



#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[cfg(not(feature = "native-clips"))]
    fn default_build_is_explicitly_runtime_independent() {
        assert!(!ClipsKernel::native_feature_enabled());
        let error = ClipsKernel.create_environment().unwrap_err();
        assert_eq!(error, ClipsKernelError::NativeFeatureDisabled);
    }

    #[test]
    #[cfg(feature = "native-clips")]
    fn native_feature_does_not_imply_a_bundled_runtime() {
        assert!(ClipsKernel::native_feature_enabled());
        if std::env::var_os("WSM_CLIPS_LIBRARY").is_none() {
            let _ = ClipsKernel::discover();
        }
    }
    #[test]
    fn c_abi_adapter_declares_clips_without_semantic_mapping() {
        let adapter = ClipsAbiAdapter::new(
            "(defrule seen (signal) => (assert (observed)))",
            "(signal)",
        );
        let vtable = adapter.vtable();
        assert_eq!(vtable.abi_version, WSM_KERNEL_ABI_VERSION);
        assert_eq!(vtable.kernel, WsmKernelKind::Clips);
        assert!(vtable.is_mechanically_complete());
        assert_eq!(adapter.last_semantic_id(), None);
        assert_eq!(adapter.last_fired(), None);
    }

}
