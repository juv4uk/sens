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

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum KernelHostError {
    NotRunning,
    Driver(String),
}

impl fmt::Display for KernelHostError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotRunning => write!(formatter, "kernel is not running"),
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
}

impl KernelRouter {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register(&mut self, driver: Box<dyn KernelDriver + Send>) {
        let id = driver.id().as_str().to_string();
        self.hosts.insert(id, KernelHost::new(driver));
    }

    pub fn is_registered(&self, target: &str) -> bool {
        self.hosts.contains_key(target)
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

#[cfg(test)]
mod tests {
    use super::*;

    struct OpaqueDriver {
        id: KernelId,
        prefix: &'static [u8],
        running: bool,
    }

    impl OpaqueDriver {
        fn new(id: &str, prefix: &'static [u8]) -> Self {
            Self {
                id: KernelId::new(id),
                prefix,
                running: false,
            }
        }
    }

    impl KernelDriver for OpaqueDriver {
        fn id(&self) -> KernelId {
            self.id.clone()
        }

        fn start(&mut self) -> Result<(), KernelHostError> {
            self.running = true;
            Ok(())
        }

        fn exchange(&mut self, payload: &[u8]) -> Result<Vec<u8>, KernelHostError> {
            if !self.running {
                return Err(KernelHostError::Driver("driver is stopped".into()));
            }
            let mut output = self.prefix.to_vec();
            output.extend_from_slice(payload);
            Ok(output)
        }

        fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
            Ok(self.prefix.to_vec())
        }

        fn stop(&mut self) -> Result<(), KernelHostError> {
            self.running = false;
            Ok(())
        }
    }

    #[test]
    fn lifecycle_submit_receive_restart_and_metrics_are_mechanical() {
        let mut host = KernelHost::new(OpaqueDriver::new("prolog", b"answers:"));
        assert_eq!(host.state(), LifecycleState::Stopped);
        assert_eq!(
            host.submit(None, b"parent(X,bob)".to_vec(), vec![]),
            Err(KernelHostError::NotRunning)
        );

        host.start().unwrap();
        let id = host
            .submit(
                Some(KernelId::new("lisp")),
                b"parent(X,bob)".to_vec(),
                b"fixture-1".to_vec(),
            )
            .unwrap();
        let response = host.receive().unwrap();

        assert_eq!(response.request_id, id);
        assert_eq!(response.kernel.as_str(), "prolog");
        assert_eq!(response.payload, b"answers:parent(X,bob)");
        assert_eq!(response.provenance, b"fixture-1");

        let metrics = host.measure();
        assert_eq!(metrics.requests, 1);
        assert_eq!(metrics.bytes_in, b"parent(X,bob)".len() as u64);
        assert_eq!(metrics.bytes_out, b"answers:parent(X,bob)".len() as u64);
        assert_eq!(metrics.starts, 1);

        host.restart().unwrap();
        assert_eq!(host.state(), LifecycleState::Running);
        assert_eq!(host.measure().starts, 2);
        assert_eq!(host.measure().stops, 1);
    }

    #[test]
    fn four_kernels_share_mechanism_without_sharing_result_types() {
        let mut lisp = KernelHost::new(OpaqueDriver::new("lisp", b"(value "));
        let mut clips = KernelHost::new(OpaqueDriver::new("clips", b"(wm-delta "));
        let mut prolog = KernelHost::new(OpaqueDriver::new("prolog", b"substitutions:"));
        let mut datalog = KernelHost::new(OpaqueDriver::new("datalog", b"closure:"));

        for host in [&mut lisp, &mut clips, &mut prolog, &mut datalog] {
            host.start().unwrap();
        }

        lisp.submit(None, b"3)".to_vec(), vec![]).unwrap();
        clips.submit(None, b"(asserted hot))".to_vec(), vec![]).unwrap();
        prolog.submit(None, b"X=alice;X=bob".to_vec(), vec![]).unwrap();
        datalog
            .submit(None, b"ancestor(alice,bob)".to_vec(), vec![])
            .unwrap();

        struct LispResult(Vec<u8>);
        struct ClipsResult {
            working_memory_delta: Vec<u8>,
        }
        struct PrologResults(Vec<Vec<u8>>);
        struct DatalogClosure {
            tuples: Vec<Vec<u8>>,
        }

        let lisp_result = LispResult(lisp.receive().unwrap().payload);
        let clips_result = ClipsResult {
            working_memory_delta: clips.receive().unwrap().payload,
        };
        let prolog_result = PrologResults(vec![prolog.receive().unwrap().payload]);
        let datalog_result = DatalogClosure {
            tuples: vec![datalog.receive().unwrap().payload],
        };

        assert!(lisp_result.0.starts_with(b"(value "));
        assert!(clips_result.working_memory_delta.starts_with(b"(wm-delta "));
        assert!(prolog_result.0[0].starts_with(b"substitutions:"));
        assert!(datalog_result.tuples[0].starts_with(b"closure:"));
    }

    #[test]
    fn availability_observation_is_mechanical_and_does_not_start_kernels() {
        let mut router = KernelRouter::new();
        router.record_availability(KernelAvailabilityObservation::available(
            "prolog",
            Some("bounded-version-probe".into()),
        ));
        router.record_availability(KernelAvailabilityObservation::unavailable(
            "clips",
            Some("runtime-not-installed".into()),
        ));

        let prolog = router.availability("prolog").expect("prolog observation");
        assert_eq!(prolog.state, AvailabilityState::Available);
        assert!(!prolog.started);
        assert_eq!(prolog.detail.as_deref(), Some("bounded-version-probe"));

        let clips = router.availability("clips").expect("clips observation");
        assert_eq!(clips.state, AvailabilityState::Unavailable);
        assert!(!clips.started);
        assert_eq!(clips.detail.as_deref(), Some("runtime-not-installed"));

        assert!(router.availability("datalog").is_none());
        assert!(router.registered_kernels().is_empty());
    }

    #[test]
    fn kernel_router_dispatches_across_multiple_islands() {
        let mut router = KernelRouter::new();
        router.register(Box::new(OpaqueDriver::new("prolog", b"prolog-out:")));
        router.register(Box::new(OpaqueDriver::new("datalog", b"datalog-out:")));

        assert!(router.is_registered("prolog"));
        assert!(router.is_registered("datalog"));
        assert!(!router.is_registered("clips"));
        assert_eq!(router.registered_kernels(), vec!["datalog", "prolog"]);

        let p_out = router.exchange("prolog", b"query1", b"prov1").unwrap();
        assert_eq!(p_out, b"prolog-out:query1");

        let d_out = router.exchange("datalog", b"facts1", b"prov2").unwrap();
        assert_eq!(d_out, b"datalog-out:facts1");

        let err = router.exchange("unknown", b"x", b"y");
        assert!(err.is_err());
    }
}
