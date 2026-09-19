//! Mechanical host substrate for autonomous reasoning kernels.
//!
//! This crate deliberately owns **no shared semantic value model**. A kernel
//! receives and returns opaque bytes. Lisp, CLIPS, Prolog, Datalog, or any
//! future island remains responsible for interpreting its own payloads.
//!
//! Common authority here is limited to mechanism: lifecycle, request identity,
//! transport metadata, snapshots, and measurements.

use std::collections::VecDeque;
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
pub trait KernelDriver {
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

/// A router managing multiple registered autonomous kernel drivers.
/// The router performs mechanical dispatch without imposing semantic interpretations.
pub struct KernelRouter {
    kernels: std::collections::HashMap<String, KernelHost<Box<dyn KernelDriver + Send>>>,
}

impl Default for KernelRouter {
    fn default() -> Self {
        Self::new()
    }
}

impl KernelRouter {
    pub fn new() -> Self {
        Self {
            kernels: std::collections::HashMap::new(),
        }
    }

    pub fn register(&mut self, driver: Box<dyn KernelDriver + Send>) -> Result<(), KernelHostError> {
        let name = driver.id().as_str().to_string();
        let mut host = KernelHost::new(driver);
        host.start()?;
        self.kernels.insert(name, host);
        Ok(())
    }

    pub fn exchange(
        &mut self,
        target: &str,
        payload: &[u8],
        provenance: &[u8],
    ) -> Result<Vec<u8>, KernelHostError> {
        let host = self
            .kernels
            .get_mut(target)
            .ok_or_else(|| KernelHostError::Driver(format!("unknown target kernel: '{target}'")))?;
        host.submit(None, payload.to_vec(), provenance.to_vec())?;
        let response = host
            .receive()
            .ok_or_else(|| KernelHostError::Driver("no response received from kernel host".into()))?;
        Ok(response.payload)
    }

    pub fn registered_kernels(&self) -> Vec<String> {
        let mut keys: Vec<String> = self.kernels.keys().cloned().collect();
        keys.sort();
        keys
    }
}

/// Status of an island call outcome under Issue #749 contract.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum IslandCallStatus {
    /// 0 answers (goal unprovable / empty relation / failure).
    None,
    /// Exactly 1 answer (deterministic evaluation / single solution).
    One,
    /// N answers (multiple solutions / relation table / agenda firings).
    Many,
    /// Boundary transport or driver error.
    Error(String),
}

/// A structured, honest response envelope representing an island call result.
/// Distinguishes between zero answers and a single answer that is the literal `()`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IslandResponseEnvelope {
    pub status: IslandCallStatus,
    pub count: usize,
    pub items: Vec<String>,
    pub raw_payload: Vec<u8>,
    pub provenance: String,
}

impl IslandResponseEnvelope {
    pub fn none(raw_payload: impl Into<Vec<u8>>, provenance: impl Into<String>) -> Self {
        Self {
            status: IslandCallStatus::None,
            count: 0,
            items: Vec::new(),
            raw_payload: raw_payload.into(),
            provenance: provenance.into(),
        }
    }

    pub fn one(item: impl Into<String>, raw_payload: impl Into<Vec<u8>>, provenance: impl Into<String>) -> Self {
        let item_str = item.into();
        Self {
            status: IslandCallStatus::One,
            count: 1,
            items: vec![item_str],
            raw_payload: raw_payload.into(),
            provenance: provenance.into(),
        }
    }

    pub fn many(items: Vec<String>, raw_payload: impl Into<Vec<u8>>, provenance: impl Into<String>) -> Self {
        let count = items.len();
        Self {
            status: IslandCallStatus::Many,
            count,
            items,
            raw_payload: raw_payload.into(),
            provenance: provenance.into(),
        }
    }

    pub fn error(message: impl Into<String>, raw_payload: impl Into<Vec<u8>>, provenance: impl Into<String>) -> Self {
        let msg = message.into();
        Self {
            status: IslandCallStatus::Error(msg),
            count: 0,
            items: Vec::new(),
            raw_payload: raw_payload.into(),
            provenance: provenance.into(),
        }
    }

    /// Formats the envelope as a canonical my-lisp s-expression.
    /// Distinguishes :none (items ()) from :one with empty list (items (())).
    pub fn to_lisp_s_expression(&self) -> String {
        match &self.status {
            IslandCallStatus::None => {
                format!(
                    "(island-result :status :none :count 0 :items () :provenance \"{}\")",
                    self.provenance
                )
            }
            IslandCallStatus::One => {
                format!(
                    "(island-result :status :one :count 1 :items ({}) :provenance \"{}\")",
                    self.items.first().map(|s| s.as_str()).unwrap_or("()"),
                    self.provenance
                )
            }
            IslandCallStatus::Many => {
                let items_str = self.items.join(" ");
                format!(
                    "(island-result :status :many :count {} :items ({}) :provenance \"{}\")",
                    self.count,
                    items_str,
                    self.provenance
                )
            }
            IslandCallStatus::Error(msg) => {
                format!(
                    "(island-result :status :error :reason \"{}\" :count 0 :items () :provenance \"{}\")",
                    msg, self.provenance
                )
            }
        }
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
    fn kernel_router_dispatches_across_multiple_islands() {
        let mut router = KernelRouter::new();
        router
            .register(Box::new(OpaqueDriver::new("prolog", b"prolog:")))
            .unwrap();
        router
            .register(Box::new(OpaqueDriver::new("datalog", b"datalog:")))
            .unwrap();

        assert_eq!(
            router.registered_kernels(),
            vec!["datalog".to_string(), "prolog".to_string()]
        );

        let p_res = router
            .exchange("prolog", b"query(1)", b"prov-1")
            .unwrap();
        assert_eq!(p_res, b"prolog:query(1)");

        let d_res = router
            .exchange("datalog", b"reach(a,b)", b"prov-2")
            .unwrap();
        assert_eq!(d_res, b"datalog:reach(a,b)");

        let err = router.exchange("unknown", b"x", b"");
        assert!(err.is_err());
    }

    #[test]
    fn island_response_envelope_distinguishes_zero_one_and_many_answers() {
        // 0-answers (failure / unprovable / empty relation)
        let env_none = IslandResponseEnvelope::none(b"", "prolog");
        assert_eq!(env_none.status, IslandCallStatus::None);
        assert_eq!(env_none.count, 0);
        assert_eq!(
            env_none.to_lisp_s_expression(),
            "(island-result :status :none :count 0 :items () :provenance \"prolog\")"
        );

        // 1-answer where the answer is the literal ()
        let env_one_empty = IslandResponseEnvelope::one("()", b"()", "common-lisp");
        assert_eq!(env_one_empty.status, IslandCallStatus::One);
        assert_eq!(env_one_empty.count, 1);
        assert_eq!(
            env_one_empty.to_lisp_s_expression(),
            "(island-result :status :one :count 1 :items (()) :provenance \"common-lisp\")"
        );

        // 1-answer with a concrete datum
        let env_one = IslandResponseEnvelope::one("42", b"42", "common-lisp");
        assert_eq!(env_one.status, IslandCallStatus::One);
        assert_eq!(env_one.count, 1);
        assert_eq!(
            env_one.to_lisp_s_expression(),
            "(island-result :status :one :count 1 :items (42) :provenance \"common-lisp\")"
        );

        // N-answers (multiple solutions from Prolog or tuples from Datalog)
        let env_many = IslandResponseEnvelope::many(
            vec!["(reach a b)".to_string(), "(reach b c)".to_string(), "(reach a c)".to_string()],
            b"3-tuples",
            "datalog",
        );
        assert_eq!(env_many.status, IslandCallStatus::Many);
        assert_eq!(env_many.count, 3);
        assert_eq!(
            env_many.to_lisp_s_expression(),
            "(island-result :status :many :count 3 :items ((reach a b) (reach b c) (reach a c)) :provenance \"datalog\")"
        );

        // Error path
        let env_err = IslandResponseEnvelope::error("syntax error", b"err", "clips");
        assert!(matches!(env_err.status, IslandCallStatus::Error(_)));
        assert_eq!(
            env_err.to_lisp_s_expression(),
            "(island-result :status :error :reason \"syntax error\" :count 0 :items () :provenance \"clips\")"
        );
    }
}
