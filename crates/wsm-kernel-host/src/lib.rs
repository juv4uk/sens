//! Mechanical host substrate for autonomous reasoning kernels.
//!
//! This crate deliberately owns **no shared semantic value model**. A kernel
//! receives and returns opaque bytes. Lisp, CLIPS, Prolog, Datalog, or any
//! future island remains responsible for interpreting its own payloads.
//!
//! Common authority here is limited to mechanism: lifecycle, request identity,
//! transport metadata, snapshots, and measurements.

use std::collections::{HashMap, VecDeque};
use std::fmt;
use std::time::Instant;

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct KernelId(String);

impl KernelId {
    pub fn new(value: impl Into<String>) -> Self {
        Self(value.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct KernelRequest {
    pub request_id: u64,
    pub source: Option<KernelId>,
    pub target: KernelId,
    pub payload: Vec<u8>,
    /// Opaque transport provenance. The host records it but never interprets it.
    pub provenance: Vec<u8>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct KernelResponse {
    pub request_id: u64,
    pub kernel: KernelId,
    pub payload: Vec<u8>,
    /// Opaque kernel/bridge provenance. No semantic schema is imposed here.
    pub provenance: Vec<u8>,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct KernelMetrics {
    pub requests: u64,
    pub bytes_in: u64,
    pub bytes_out: u64,
    pub elapsed_ns: u128,
    pub starts: u64,
    pub stops: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LifecycleState {
    Stopped,
    Running,
}

/// Mechanical execution availability reported by a producer-specific bounded probe.
///
/// This is not a truth value and carries no semantic authority. Unavailable
/// means only that execution cannot currently be performed by that producer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AvailabilityState {
    Available,
    Unavailable,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct KernelAvailabilityObservation {
    pub producer: KernelId,
    pub state: AvailabilityState,
    pub started: bool,
    /// Producer-supplied diagnostic/provenance text. The host never interprets it.
    pub detail: Option<String>,
}

impl KernelAvailabilityObservation {
    pub fn available(producer: impl Into<String>, detail: Option<String>) -> Self {
        Self {
            producer: KernelId::new(producer),
            state: AvailabilityState::Available,
            started: false,
            detail,
        }
    }

    pub fn unavailable(producer: impl Into<String>, detail: Option<String>) -> Self {
        Self {
            producer: KernelId::new(producer),
            state: AvailabilityState::Unavailable,
            started: false,
            detail,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct KernelHandle(u64);

impl KernelHandle {
    pub const fn new(id: u64) -> Self {
        Self(id)
    }

    pub const fn id(self) -> u64 {
        self.0
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum KernelLifecycleState {
    Loaded,
    Started,
    Stopped,
    Unloaded,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct KernelLifecycleObservation {
    pub handle: KernelHandle,
    pub producer: KernelId,
    pub state: KernelLifecycleState,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum KernelHostError {
    NotRunning,
    UnknownHandle(u64),
    InvalidLifecycle {
        action: &'static str,
        state: KernelLifecycleState,
    },
    Driver(String),
}

impl fmt::Display for KernelHostError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotRunning => write!(formatter, "kernel is not running"),
            Self::UnknownHandle(handle) => write!(formatter, "unknown kernel handle {handle}"),
            Self::InvalidLifecycle { action, state } => {
                write!(
                    formatter,
                    "cannot {action} kernel while lifecycle state is {state:?}"
                )
            }
            Self::Driver(message) => write!(formatter, "kernel driver error: {message}"),
        }
    }
}

impl std::error::Error for KernelHostError {}

/// Kernel-local mechanism. The host never asks the driver to convert a payload
/// into a common semantic Rust type.
pub trait KernelDriver: Send {
    fn id(&self) -> KernelId;
    fn start(&mut self) -> Result<(), KernelHostError>;
    fn exchange(&mut self, payload: &[u8]) -> Result<Vec<u8>, KernelHostError>;
    fn snapshot(&self) -> Result<Vec<u8>, KernelHostError>;
    fn stop(&mut self) -> Result<(), KernelHostError>;
}

pub struct KernelHost<D> {
    driver: D,
    state: LifecycleState,
    next_request_id: u64,
    pending: VecDeque<KernelResponse>,
    metrics: KernelMetrics,
}

impl<D: KernelDriver> KernelHost<D> {
    pub fn new(driver: D) -> Self {
        Self {
            driver,
            state: LifecycleState::Stopped,
            next_request_id: 1,
            pending: VecDeque::new(),
            metrics: KernelMetrics::default(),
        }
    }

    pub fn id(&self) -> KernelId {
        self.driver.id()
    }

    pub fn state(&self) -> LifecycleState {
        self.state
    }

    pub fn start(&mut self) -> Result<(), KernelHostError> {
        if self.state == LifecycleState::Running {
            return Ok(());
        }
        self.driver.start()?;
        self.state = LifecycleState::Running;
        self.metrics.starts += 1;
        Ok(())
    }

    pub fn submit(
        &mut self,
        source: Option<KernelId>,
        payload: Vec<u8>,
        provenance: Vec<u8>,
    ) -> Result<u64, KernelHostError> {
        if self.state != LifecycleState::Running {
            return Err(KernelHostError::NotRunning);
        }

        let request_id = self.next_request_id;
        self.next_request_id += 1;
        let target = self.driver.id();
        let request = KernelRequest {
            request_id,
            source,
            target: target.clone(),
            payload,
            provenance,
        };

        let started = Instant::now();
        let output = self.driver.exchange(&request.payload)?;
        self.metrics.elapsed_ns += started.elapsed().as_nanos();
        self.metrics.requests += 1;
        self.metrics.bytes_in += request.payload.len() as u64;
        self.metrics.bytes_out += output.len() as u64;

        self.pending.push_back(KernelResponse {
            request_id,
            kernel: target,
            payload: output,
            provenance: request.provenance,
        });
        Ok(request_id)
    }

    pub fn receive(&mut self) -> Option<KernelResponse> {
        self.pending.pop_front()
    }

    pub fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
        if self.state != LifecycleState::Running {
            return Err(KernelHostError::NotRunning);
        }
        self.driver.snapshot()
    }

    pub fn stop(&mut self) -> Result<(), KernelHostError> {
        if self.state == LifecycleState::Stopped {
            return Ok(());
        }
        self.driver.stop()?;
        self.state = LifecycleState::Stopped;
        self.metrics.stops += 1;
        Ok(())
    }

    pub fn restart(&mut self) -> Result<(), KernelHostError> {
        self.stop()?;
        self.start()
    }

    pub fn measure(&self) -> KernelMetrics {
        self.metrics.clone()
    }

    pub fn into_driver(self) -> D {
        self.driver
    }
}

impl<D: ?Sized + KernelDriver + Send> KernelDriver for Box<D> {
    fn id(&self) -> KernelId {
        (**self).id()
    }

    fn start(&mut self) -> Result<(), KernelHostError> {
        (**self).start()
    }

    fn exchange(&mut self, payload: &[u8]) -> Result<Vec<u8>, KernelHostError> {
        (**self).exchange(payload)
    }

    fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
        (**self).snapshot()
    }

    fn stop(&mut self) -> Result<(), KernelHostError> {
        (**self).stop()
    }
}

/// Multi-kernel router for mechanical dispatch across autonomous reasoning islands.
///
/// Owns no semantics, truth model, or payload translation. Opaque bytes in,
/// opaque bytes out.
#[derive(Default)]
pub struct KernelRouter {
    hosts: HashMap<String, KernelHost<Box<dyn KernelDriver + Send>>>,
    availability: HashMap<String, KernelAvailabilityObservation>,
    next_handle_id: u64,
    handles: HashMap<KernelHandle, KernelLifecycleObservation>,
    target_handles: HashMap<String, KernelHandle>,
}

impl KernelRouter {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn load(&mut self, driver: Box<dyn KernelDriver + Send>) -> KernelHandle {
        let producer = driver.id();
        let target = producer.as_str().to_string();

        if let Some(previous) = self.target_handles.remove(&target) {
            self.hosts.remove(&target);
            if let Some(observation) = self.handles.get_mut(&previous) {
                observation.state = KernelLifecycleState::Unloaded;
            }
        }

        self.next_handle_id = self
            .next_handle_id
            .checked_add(1)
            .expect("kernel handle counter exhausted");
        let handle = KernelHandle::new(self.next_handle_id);

        self.hosts.insert(target.clone(), KernelHost::new(driver));
        self.target_handles.insert(target, handle);
        self.handles.insert(
            handle,
            KernelLifecycleObservation {
                handle,
                producer,
                state: KernelLifecycleState::Loaded,
            },
        );
        handle
    }

    /// Compatibility entry point. New orchestration should prefer load so
    /// the mechanical runtime instance remains addressable by handle.
    pub fn register(&mut self, driver: Box<dyn KernelDriver + Send>) {
        let _ = self.load(driver);
    }

    pub fn is_registered(&self, target: &str) -> bool {
        self.hosts.contains_key(target)
    }

    pub fn handle_for(&self, target: &str) -> Option<KernelHandle> {
        self.target_handles.get(target).copied()
    }

    pub fn lifecycle(&self, handle: KernelHandle) -> Option<&KernelLifecycleObservation> {
        self.handles.get(&handle)
    }

    pub fn start_handle(&mut self, handle: KernelHandle) -> Result<(), KernelHostError> {
        let (target, state) = {
            let observation = self
                .handles
                .get(&handle)
                .ok_or(KernelHostError::UnknownHandle(handle.id()))?;
            (observation.producer.as_str().to_string(), observation.state)
        };

        match state {
            KernelLifecycleState::Started => return Ok(()),
            KernelLifecycleState::Unloaded => {
                return Err(KernelHostError::InvalidLifecycle {
                    action: "start",
                    state,
                });
            }
            KernelLifecycleState::Loaded | KernelLifecycleState::Stopped => {}
        }

        let host = self.hosts.get_mut(&target).ok_or_else(|| {
            KernelHostError::Driver(format!("loaded kernel '{target}' has no host"))
        })?;
        host.start()?;
        self.handles
            .get_mut(&handle)
            .expect("checked handle must still exist")
            .state = KernelLifecycleState::Started;
        Ok(())
    }

    pub fn invoke_handle(
        &mut self,
        handle: KernelHandle,
        payload: &[u8],
        provenance: &[u8],
    ) -> Result<KernelResponse, KernelHostError> {
        let (target, state) = {
            let observation = self
                .handles
                .get(&handle)
                .ok_or(KernelHostError::UnknownHandle(handle.id()))?;
            (observation.producer.as_str().to_string(), observation.state)
        };

        if state != KernelLifecycleState::Started {
            return Err(KernelHostError::InvalidLifecycle {
                action: "invoke",
                state,
            });
        }

        let host = self.hosts.get_mut(&target).ok_or_else(|| {
            KernelHostError::Driver(format!("started kernel '{target}' has no host"))
        })?;
        let _request_id = host.submit(None, payload.to_vec(), provenance.to_vec())?;
        host.receive().ok_or_else(|| {
            KernelHostError::Driver(format!("no response received from kernel '{target}'"))
        })
    }

    pub fn stop_handle(&mut self, handle: KernelHandle) -> Result<(), KernelHostError> {
        let (target, state) = {
            let observation = self
                .handles
                .get(&handle)
                .ok_or(KernelHostError::UnknownHandle(handle.id()))?;
            (observation.producer.as_str().to_string(), observation.state)
        };

        match state {
            KernelLifecycleState::Unloaded => return Ok(()),
            KernelLifecycleState::Loaded | KernelLifecycleState::Stopped => {
                self.handles
                    .get_mut(&handle)
                    .expect("checked handle must still exist")
                    .state = KernelLifecycleState::Stopped;
                return Ok(());
            }
            KernelLifecycleState::Started => {}
        }

        let host = self.hosts.get_mut(&target).ok_or_else(|| {
            KernelHostError::Driver(format!("started kernel '{target}' has no host"))
        })?;
        host.stop()?;
        self.handles
            .get_mut(&handle)
            .expect("checked handle must still exist")
            .state = KernelLifecycleState::Stopped;
        Ok(())
    }

    pub fn unload_handle(&mut self, handle: KernelHandle) -> Result<(), KernelHostError> {
        let (target, state) = {
            let observation = self
                .handles
                .get(&handle)
                .ok_or(KernelHostError::UnknownHandle(handle.id()))?;
            (observation.producer.as_str().to_string(), observation.state)
        };

        if state == KernelLifecycleState::Unloaded {
            return Ok(());
        }
        if state == KernelLifecycleState::Started {
            return Err(KernelHostError::InvalidLifecycle {
                action: "unload",
                state,
            });
        }

        self.hosts.remove(&target);
        if self.target_handles.get(&target).copied() == Some(handle) {
            self.target_handles.remove(&target);
        }
        self.handles
            .get_mut(&handle)
            .expect("checked handle must still exist")
            .state = KernelLifecycleState::Unloaded;
        Ok(())
    }

    /// Record a producer-specific bounded availability probe through one
    /// mechanical host path. Recording does not start a kernel.
    pub fn record_availability(&mut self, observation: KernelAvailabilityObservation) {
        self.availability
            .insert(observation.producer.as_str().to_string(), observation);
    }

    pub fn availability(&self, target: &str) -> Option<&KernelAvailabilityObservation> {
        self.availability.get(target)
    }

    pub fn exchange(
        &mut self,
        target: &str,
        payload: &[u8],
        provenance: &[u8],
    ) -> Result<Vec<u8>, KernelHostError> {
        let host = self.hosts.get_mut(target).ok_or_else(|| {
            KernelHostError::Driver(format!("target kernel '{target}' is not registered"))
        })?;
        if host.state() != LifecycleState::Running {
            host.start()?;
        }
        let _req_id = host.submit(None, payload.to_vec(), provenance.to_vec())?;
        let resp = host.receive().ok_or_else(|| {
            KernelHostError::Driver(format!("no response received from kernel '{target}'"))
        })?;
        Ok(resp.payload)
    }

    pub fn registered_kernels(&self) -> Vec<String> {
        let mut keys: Vec<String> = self.hosts.keys().cloned().collect();
        keys.sort();
        keys
    }
}

