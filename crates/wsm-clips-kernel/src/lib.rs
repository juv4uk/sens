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

use std::fmt;

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
    BuildFailed(i32),
    #[cfg(feature = "native-clips")]
    AssertFailed,
    #[cfg(feature = "native-clips")]
    RetractFailed(i32),
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
    use std::ffi::{c_char, c_longlong, c_void, CStr, CString, OsStr};
    use std::sync::Arc;

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
    type BuildFn = unsafe extern "C" fn(*mut Environment, *const c_char) -> i32;
    type AssertStringFn = unsafe extern "C" fn(*mut Environment, *const c_char) -> *mut Fact;
    type RunFn = unsafe extern "C" fn(*mut Environment, c_longlong) -> c_longlong;
    type RetractFn = unsafe extern "C" fn(*mut Fact) -> i32;
    type RetainFactFn = unsafe extern "C" fn(*mut Environment, *mut Fact);
    type ReleaseFactFn = unsafe extern "C" fn(*mut Environment, *mut Fact);

    #[cfg(unix)]
    mod loader {
        use super::*;

        const RTLD_NOW: i32 = 2;

        #[cfg_attr(not(target_os = "macos"), link(name = "dl"))]
        unsafe extern "C" {
            fn dlopen(filename: *const c_char, flags: i32) -> *mut c_void;
            fn dlsym(handle: *mut c_void, symbol: *const c_char) -> *mut c_void;
            fn dlclose(handle: *mut c_void) -> i32;
            fn dlerror() -> *const c_char;
        }

        pub struct DynamicLibrary {
            handle: *mut c_void,
        }

        impl DynamicLibrary {
            pub unsafe fn open(path: &OsStr) -> Result<Self, String> {
                use std::os::unix::ffi::OsStrExt;
                let path = CString::new(path.as_bytes())
                    .map_err(|_| "library path contains an interior NUL byte".to_string())?;
                let handle = unsafe { dlopen(path.as_ptr(), RTLD_NOW) };
                if handle.is_null() {
                    return Err(last_error());
                }
                Ok(Self { handle })
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
        pub retain_fact: RetainFactFn,
        pub release_fact: ReleaseFactFn,
    }

    impl NativeApi {
        pub unsafe fn load(path: impl AsRef<OsStr>) -> Result<Arc<Self>, ClipsKernelError> {
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
            let retain_fact = unsafe { load_symbol(&library, b"RetainFact\0")? };
            let release_fact = unsafe { load_symbol(&library, b"ReleaseFact\0")? };

            Ok(Arc::new(Self {
                _library: library,
                create_environment,
                destroy_environment,
                build,
                assert_string,
                run,
                retract,
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
    api: std::sync::Arc<native::NativeApi>,
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
            api: self.api.clone(),
            raw,
        })
    }
}

#[cfg(feature = "native-clips")]
pub struct ClipsEnvironment {
    api: std::sync::Arc<native::NativeApi>,
    raw: *mut native::Environment,
}

#[cfg(feature = "native-clips")]
impl ClipsEnvironment {
    pub fn build(&self, construct: &str) -> Result<(), ClipsKernelError> {
        let construct =
            std::ffi::CString::new(construct).map_err(|_| ClipsKernelError::NulInput)?;
        let code = unsafe { (self.api.build)(self.raw, construct.as_ptr()) };
        if code == 0 {
            Ok(())
        } else {
            Err(ClipsKernelError::BuildFailed(code))
        }
    }

    pub fn assert_string<'env>(
        &'env self,
        fact: &str,
    ) -> Result<ClipsFact<'env>, ClipsKernelError> {
        let fact = std::ffi::CString::new(fact).map_err(|_| ClipsKernelError::NulInput)?;
        let raw = unsafe { (self.api.assert_string)(self.raw, fact.as_ptr()) };
        if raw.is_null() {
            Err(ClipsKernelError::AssertFailed)
        } else {
            unsafe { (self.api.retain_fact)(self.raw, raw) };
            Ok(ClipsFact {
                api: self.api.clone(),
                env: self.raw,
                raw,
                retained: true,
                _environment: std::marker::PhantomData,
            })
        }
    }

    pub fn run(&self, limit: i64) -> i64 {
        unsafe { (self.api.run)(self.raw, limit) }
    }

    pub fn retract(&self, mut fact: ClipsFact<'_>) -> Result<(), ClipsKernelError> {
        let raw = fact.raw;
        if fact.retained {
            unsafe { (self.api.release_fact)(self.raw, raw) };
            fact.retained = false;
        }
        let code = unsafe { (self.api.retract)(raw) };
        if code == 0 {
            Ok(())
        } else {
            Err(ClipsKernelError::RetractFailed(code))
        }
    }
}

#[cfg(feature = "native-clips")]
impl Drop for ClipsEnvironment {
    fn drop(&mut self) {
        if !self.raw.is_null() {
            let _ = unsafe { (self.api.destroy_environment)(self.raw) };
            self.raw = std::ptr::null_mut();
        }
    }
}

#[cfg(feature = "native-clips")]
pub struct ClipsFact<'env> {
    api: std::sync::Arc<native::NativeApi>,
    env: *mut native::Environment,
    raw: *mut native::Fact,
    retained: bool,
    _environment: std::marker::PhantomData<&'env ClipsEnvironment>,
}

#[cfg(feature = "native-clips")]
impl Drop for ClipsFact<'_> {
    fn drop(&mut self) {
        if self.retained && !self.raw.is_null() {
            unsafe { (self.api.release_fact)(self.env, self.raw) };
            self.retained = false;
        }
    }
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
}
