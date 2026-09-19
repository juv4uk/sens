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
}
