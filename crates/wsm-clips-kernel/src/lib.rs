//! Native CLIPS island boundary.
//!
//! This crate owns only mechanical access to the external CLIPS C runtime.
//! It does not reimplement CLIPS semantics and does not assign meaning to
//! my-lisp semantic IDs.
//!
//! The default build deliberately does not link CLIPS. Enable the
//! `native-clips` feature only in an environment that provides the CLIPS
//! C library. This keeps the my-lisp release independent from the external
//! runtime while preserving a direct native C boundary.

use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClipsKernelError {
    NativeFeatureDisabled,
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

/// Mechanical CLIPS runtime boundary.
///
/// Without the `native-clips` feature this type is intentionally inert and
/// reports a named unavailable state instead of pretending that CLIPS exists.
#[derive(Debug, Default)]
pub struct ClipsKernel;

impl ClipsKernel {
    pub const fn native_feature_enabled() -> bool {
        cfg!(feature = "native-clips")
    }

    #[cfg(not(feature = "native-clips"))]
    pub fn create_environment(&self) -> Result<(), ClipsKernelError> {
        Err(ClipsKernelError::NativeFeatureDisabled)
    }

    #[cfg(feature = "native-clips")]
    pub fn create_environment(&self) -> Result<ClipsEnvironment, ClipsKernelError> {
        ClipsEnvironment::new()
    }
}

#[cfg(feature = "native-clips")]
mod native {
    use std::ffi::{c_char, c_longlong};

    #[repr(C)]
    pub struct Environment {
        _private: [u8; 0],
    }

    #[repr(C)]
    pub struct Fact {
        _private: [u8; 0],
    }

    #[link(name = "clips")]
    unsafe extern "C" {
        pub fn CreateEnvironment() -> *mut Environment;
        pub fn DestroyEnvironment(env: *mut Environment) -> bool;
        pub fn Build(env: *mut Environment, construct: *const c_char) -> i32;
        pub fn AssertString(env: *mut Environment, fact: *const c_char) -> *mut Fact;
        pub fn Run(env: *mut Environment, run_limit: c_longlong) -> c_longlong;
        pub fn Retract(fact: *mut Fact) -> i32;
        pub fn RetainFact(env: *mut Environment, fact: *mut Fact);
        pub fn ReleaseFact(env: *mut Environment, fact: *mut Fact);
    }
}

#[cfg(feature = "native-clips")]
pub struct ClipsEnvironment {
    raw: *mut native::Environment,
}

#[cfg(feature = "native-clips")]
impl ClipsEnvironment {
    fn new() -> Result<Self, ClipsKernelError> {
        let raw = unsafe { native::CreateEnvironment() };
        if raw.is_null() {
            return Err(ClipsKernelError::CreateEnvironmentFailed);
        }
        Ok(Self { raw })
    }

    pub fn build(&self, construct: &str) -> Result<(), ClipsKernelError> {
        let construct =
            std::ffi::CString::new(construct).map_err(|_| ClipsKernelError::NulInput)?;
        let code = unsafe { native::Build(self.raw, construct.as_ptr()) };
        if code == 0 {
            Ok(())
        } else {
            Err(ClipsKernelError::BuildFailed(code))
        }
    }

    pub fn assert_string<'env>(&'env self, fact: &str) -> Result<ClipsFact<'env>, ClipsKernelError> {
        let fact = std::ffi::CString::new(fact).map_err(|_| ClipsKernelError::NulInput)?;
        let raw = unsafe { native::AssertString(self.raw, fact.as_ptr()) };
        if raw.is_null() {
            Err(ClipsKernelError::AssertFailed)
        } else {
            unsafe { native::RetainFact(self.raw, raw) };
            Ok(ClipsFact {
                env: self.raw,
                raw,
                retained: true,
                _environment: std::marker::PhantomData,
            })
        }
    }

    pub fn run(&self, limit: i64) -> i64 {
        unsafe { native::Run(self.raw, limit) }
    }

    pub fn retract(&self, mut fact: ClipsFact<'_>) -> Result<(), ClipsKernelError> {
        let raw = fact.raw;
        if fact.retained {
            unsafe { native::ReleaseFact(self.raw, raw) };
            fact.retained = false;
        }
        let code = unsafe { native::Retract(raw) };
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
            let _ = unsafe { native::DestroyEnvironment(self.raw) };
            self.raw = std::ptr::null_mut();
        }
    }
}

#[cfg(feature = "native-clips")]
pub struct ClipsFact<'env> {
    env: *mut native::Environment,
    raw: *mut native::Fact,
    retained: bool,
    _environment: std::marker::PhantomData<&'env ClipsEnvironment>,
}

#[cfg(feature = "native-clips")]
impl Drop for ClipsFact<'_> {
    fn drop(&mut self) {
        if self.retained && !self.raw.is_null() {
            unsafe { native::ReleaseFact(self.env, self.raw) };
            self.retained = false;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_build_is_explicitly_runtime_independent() {
        assert!(!ClipsKernel::native_feature_enabled());
        let error = ClipsKernel.create_environment().unwrap_err();
        assert_eq!(error, ClipsKernelError::NativeFeatureDisabled);
    }
}
