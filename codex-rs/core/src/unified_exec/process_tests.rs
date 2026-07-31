use super::process::NoopSpawnLifecycle;
use super::process::UnifiedExecProcess;
use crate::unified_exec::UnifiedExecError;
use codex_exec_server::ExecProcess;
use codex_exec_server::ExecProcessEventReceiver;
use codex_exec_server::ExecProcessFuture;
use codex_exec_server::ExecServerError;
use codex_exec_server::ProcessId;
use codex_exec_server::ProcessSignal;
use codex_exec_server::ReadResponse;
use codex_exec_server::StartedExecProcess;
use codex_exec_server::WriteResponse;
use codex_exec_server::WriteStatus;
use codex_utils_pty::ProcessDriver;
use codex_utils_pty::spawn_from_driver;
use pretty_assertions::assert_eq;
use std::collections::VecDeque;
use std::sync::Arc;
use std::sync::atomic::Ordering;
use std::time::Duration;
use tokio::sync::Mutex;
use tokio::sync::broadcast;
use tokio::sync::mpsc;
use tokio::sync::oneshot;
use tokio::sync::watch;

struct MockExecProcess {
    process_id: ProcessId,
    write_response: WriteResponse,
    read_responses: Mutex<VecDeque<ReadResponse>>,
    terminate_error: Option<String>,
    wake_tx: watch::Sender<u64>,
}

impl MockExecProcess {
    async fn read(&self) -> Result<ReadResponse, ExecServerError> {
        Ok(self
            .read_responses
            .lock()
            .await
            .pop_front()
            .unwrap_or(ReadResponse {
                chunks: Vec::new(),
                next_seq: 1,
                exited: false,
                exit_code: None,
                closed: false,
                failure: None,
                sandbox_denied: false,
            }))
    }

    async fn terminate(&self) -> Result<(), ExecServerError> {
        if let Some(message) = &self.terminate_error {
            return Err(ExecServerError::Protocol(message.clone()));
        }
        Ok(())
    }
}

impl ExecProcess for MockExecProcess {
    fn process_id(&self) -> &ProcessId {
        &self.process_id
    }

    fn subscribe_wake(&self) -> watch::Receiver<u64> {
        self.wake_tx.subscribe()
    }

    fn subscribe_events(&self) -> ExecProcessEventReceiver {
        ExecProcessEventReceiver::empty()
    }

    fn read(
        &self,
        _after_seq: Option<u64>,
        _max_bytes: Option<usize>,
        _wait_ms: Option<u64>,
    ) -> ExecProcessFuture<'_, ReadResponse> {
        Box::pin(MockExecProcess::read(self))
    }

    fn write(&self, _chunk: Vec<u8>) -> ExecProcessFuture<'_, WriteResponse> {
        Box::pin(async { Ok(self.write_response.clone()) })
    }

    fn signal(&self, _signal: ProcessSignal) -> ExecProcessFuture<'_, ()> {
        Box::pin(async { Ok(()) })
    }

    fn terminate(&self) -> ExecProcessFuture<'_, ()> {
        Box::pin(MockExecProcess::terminate(self))
    }
}

pub(super) async fn remote_process(
    write_status: WriteStatus,
    terminate_error: Option<String>,
    sandbox_type: codex_sandboxing::SandboxType,
) -> UnifiedExecProcess {
    let (wake_tx, _wake_rx) = watch::channel(0);
    let started = StartedExecProcess {
        process: Arc::new(MockExecProcess {
            process_id: "test-process".to_string().into(),
            write_response: WriteResponse {
                status: write_status,
            },
            read_responses: Mutex::new(VecDeque::new()),
            terminate_error,
            wake_tx,
        }),
        sandbox_type: Some(sandbox_type),
    };

    UnifiedExecProcess::from_exec_server_started(started)
        .await
        .expect("remote process should start")
}

#[tokio::test]
async fn remote_write_unknown_process_marks_process_exited() {
    let process = remote_process(
        WriteStatus::UnknownProcess,
        /*terminate_error*/ None,
        codex_sandboxing::SandboxType::None,
    )
    .await;

    let err = process
        .write(b"hello")
        .await
        .expect_err("expected write failure");

    assert!(matches!(err, UnifiedExecError::WriteToStdin));
    assert!(process.has_exited());
}

#[tokio::test]
async fn remote_write_closed_stdin_marks_process_exited() {
    let process = remote_process(
        WriteStatus::StdinClosed,
        /*terminate_error*/ None,
        codex_sandboxing::SandboxType::None,
    )
    .await;

    let err = process
        .write(b"hello")
        .await
        .expect_err("expected write failure");

    assert!(matches!(err, UnifiedExecError::WriteToStdin));
    assert!(process.has_exited());
}

#[tokio::test]
async fn fail_and_terminate_preserves_failure_message() {
    let process = remote_process(
        WriteStatus::Accepted,
        /*terminate_error*/ None,
        codex_sandboxing::SandboxType::None,
    )
    .await;

    process.fail_and_terminate("network denied".to_string());
    process.fail_and_terminate("second failure".to_string());

    assert!(process.has_exited());
    assert_eq!(
        process.failure_message(),
        Some("network denied".to_string())
    );
}

#[tokio::test]
async fn remote_terminate_confirmed_updates_state_on_success_only() {
    let process = remote_process(
        WriteStatus::Accepted,
        Some("terminate unavailable".to_string()),
        codex_sandboxing::SandboxType::None,
    )
    .await;

    let err = process
        .terminate_confirmed()
        .await
        .expect_err("expected terminate failure");

    assert!(matches!(err, UnifiedExecError::ProcessFailed { .. }));
    assert!(!process.has_exited());

    let process = remote_process(
        WriteStatus::Accepted,
        /*terminate_error*/ None,
        codex_sandboxing::SandboxType::None,
    )
    .await;

    process
        .terminate_confirmed()
        .await
        .expect("terminate should succeed");

    assert!(process.has_exited());
}

#[tokio::test]
async fn remote_process_preserves_executor_sandbox_type() {
    let process = remote_process(
        WriteStatus::Accepted,
        /*terminate_error*/ None,
        codex_sandboxing::SandboxType::LinuxSeccomp,
    )
    .await;

    assert_eq!(
        process.sandbox_type(),
        codex_sandboxing::SandboxType::LinuxSeccomp
    );
}

async fn local_output_process() -> (
    UnifiedExecProcess,
    broadcast::Sender<Vec<u8>>,
    oneshot::Sender<i32>,
) {
    let (writer_tx, _writer_rx) = mpsc::channel(1);
    let (stdout_tx, stdout_rx) = broadcast::channel(512);
    let (exit_tx, exit_rx) = oneshot::channel();
    let spawned = spawn_from_driver(ProcessDriver {
        writer_tx,
        stdout_rx,
        stderr_rx: None,
        exit_rx,
        terminator: None,
        writer_handle: None,
        resizer: None,
    });
    let process = UnifiedExecProcess::from_spawned(
        spawned,
        codex_sandboxing::SandboxType::None,
        Box::new(NoopSpawnLifecycle),
    )
    .await
    .expect("driver-backed local process should start");
    (process, stdout_tx, exit_tx)
}

async fn wait_for_local_output_close(process: &UnifiedExecProcess) {
    let output_handles = process.output_handles();
    tokio::time::timeout(Duration::from_secs(5), async {
        while !output_handles.output_closed.load(Ordering::Acquire) {
            tokio::task::yield_now().await;
        }
    })
    .await
    .expect("local output task should close");
}

#[tokio::test]
async fn local_output_task_retains_stdout_before_best_effort_broadcast() {
    let (process, stdout_tx, exit_tx) = local_output_process().await;
    let mut lagging_receiver = process.output_receiver();
    let mut expected = Vec::new();
    for index in 0..256 {
        let chunk = format!("stdout-{index:04}\n").into_bytes();
        expected.extend_from_slice(&chunk);
        stdout_tx.send(chunk).expect("send stdout chunk");
    }
    drop(stdout_tx);
    exit_tx.send(0).expect("send exit code");
    wait_for_local_output_close(&process).await;

    assert!(matches!(
        lagging_receiver.recv().await,
        Err(broadcast::error::RecvError::Lagged(_))
    ));
    let output_handles = process.output_handles();
    assert_eq!(
        output_handles.output_buffer.lock().await.total_bytes(),
        expected.len()
    );
    assert_eq!(
        process.completion_buffer().lock().await.total_bytes(),
        expected.len()
    );
    assert_eq!(
        process
            .completion_buffer()
            .lock()
            .await
            .to_bytes_with_omission_marker(),
        expected
    );
}

#[tokio::test]
async fn local_output_task_retains_invalid_utf8_when_broadcast_lags() {
    let (process, stdout_tx, exit_tx) = local_output_process().await;
    let mut lagging_receiver = process.output_receiver();
    let mut expected = Vec::new();
    for index in 0..256 {
        let chunk = vec![0xff, (index % 251) as u8, b'\n'];
        expected.extend_from_slice(&chunk);
        stdout_tx.send(chunk).expect("send invalid UTF-8 chunk");
    }
    drop(stdout_tx);
    exit_tx.send(0).expect("send exit code");
    wait_for_local_output_close(&process).await;

    assert!(matches!(
        lagging_receiver.recv().await,
        Err(broadcast::error::RecvError::Lagged(_))
    ));
    assert_eq!(
        process
            .completion_buffer()
            .lock()
            .await
            .to_bytes_with_omission_marker(),
        expected
    );
}
