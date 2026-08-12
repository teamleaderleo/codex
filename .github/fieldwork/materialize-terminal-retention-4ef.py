from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected one match, found {count}"
    return text.replace(old, new, 1)


process_path = "codex-rs/core/src/unified_exec/process.rs"
process = read(process_path)

process = replace_once(
    process,
    "pub(crate) type OutputBuffer = Arc<Mutex<HeadTailBuffer>>;\n",
    '''#[derive(Debug, Default)]
struct OutputState {
    output: HeadTailBuffer,
    completion: HeadTailBuffer,
}

#[derive(Clone, Copy)]
enum OutputBufferKind {
    Output,
    Completion,
}

pub(crate) struct OutputBufferView {
    state: Arc<Mutex<OutputState>>,
    kind: OutputBufferKind,
}

impl OutputBufferView {
    fn new(state: Arc<Mutex<OutputState>>, kind: OutputBufferKind) -> Self {
        Self { state, kind }
    }

    pub(crate) async fn lock(&self) -> tokio::sync::MappedMutexGuard<'_, HeadTailBuffer> {
        let guard = self.state.lock().await;
        match self.kind {
            OutputBufferKind::Output => {
                tokio::sync::MutexGuard::map(guard, |state| &mut state.output)
            }
            OutputBufferKind::Completion => {
                tokio::sync::MutexGuard::map(guard, |state| &mut state.completion)
            }
        }
    }
}

pub(crate) type OutputBuffer = Arc<OutputBufferView>;
''',
    "output state",
)

process = replace_once(
    process,
    "    pub(crate) output_buffer: OutputBuffer,\n    pub(crate) output_notify: Arc<Notify>,\n",
    "    pub(crate) output_buffer: OutputBuffer,\n    pub(crate) completion_buffer: OutputBuffer,\n    pub(crate) output_notify: Arc<Notify>,\n",
    "output handles completion field",
)

process = replace_once(
    process,
    '''        let output = OutputHandles {
            output_buffer: Arc::new(Mutex::new(HeadTailBuffer::default())),
            output_notify: Arc::new(Notify::new()),
            output_closed: Arc::new(AtomicBool::new(false)),
            output_closed_notify: Arc::new(Notify::new()),
            cancellation_token: CancellationToken::new(),
        };
''',
    '''        let output_state = Arc::new(Mutex::new(OutputState::default()));
        let output = OutputHandles {
            output_buffer: Arc::new(OutputBufferView::new(
                Arc::clone(&output_state),
                OutputBufferKind::Output,
            )),
            completion_buffer: Arc::new(OutputBufferView::new(
                output_state,
                OutputBufferKind::Completion,
            )),
            output_notify: Arc::new(Notify::new()),
            output_closed: Arc::new(AtomicBool::new(false)),
            output_closed_notify: Arc::new(Notify::new()),
            cancellation_token: CancellationToken::new(),
        };
''',
    "output initialization",
)

process = replace_once(
    process,
    '''    pub(super) fn output_handles(&self) -> &OutputHandles {
        &self.output
    }

''',
    '''    pub(super) fn output_handles(&self) -> &OutputHandles {
        &self.output
    }

    pub(super) fn completion_buffer(&self) -> OutputBuffer {
        Arc::clone(&self.output.completion_buffer)
    }

''',
    "completion accessor",
)

process = replace_once(
    process,
    '''        let output_rx = codex_utils_pty::combine_output_receivers(stdout_rx, stderr_rx);
        let mut managed = Self::new(
            ProcessHandle::Local(Box::new(process_handle)),
            sandbox_type,
            Some(spawn_lifecycle),
        );
        managed.output_task = Some(Self::spawn_local_output_task(
            output_rx,
            managed.output_handles().clone(),
            managed.output_tx.clone(),
        ));
''',
    '''        let mut managed = Self::new(
            ProcessHandle::Local(Box::new(process_handle)),
            sandbox_type,
            Some(spawn_lifecycle),
        );
        managed.output_task = Some(Self::spawn_local_output_task(
            stdout_rx,
            stderr_rx,
            managed.output_handles().clone(),
            managed.output_tx.clone(),
        ));
''',
    "local source handoff",
)

marker = "    fn spawn_exec_server_output_task(\n"
assert process.count(marker) == 1, "spawn exec marker"
record_helper = '''    async fn record_output_chunk(
        output_buffer: &OutputBuffer,
        completion_buffer: &OutputBuffer,
        chunk: &[u8],
    ) {
        debug_assert!(Arc::ptr_eq(
            &output_buffer.state,
            &completion_buffer.state
        ));
        let mut state = output_buffer.state.lock().await;
        state.completion.push_chunk(chunk.to_vec());
        state.output.push_chunk(chunk.to_vec());
    }

'''
process = process.replace(marker, record_helper + marker, 1)

process = replace_once(
    process,
    '''        let OutputHandles {
            output_buffer,
            output_notify,
            output_closed,
''',
    '''        let OutputHandles {
            output_buffer,
            completion_buffer,
            output_notify,
            output_closed,
''',
    "exec output handles destructure",
)

producer_old = '''                        let mut guard = output_buffer.lock().await;
                        guard.push_chunk(bytes.clone());
                        drop(guard);
                        let _ = output_tx.send(bytes);
'''
producer_new = '''                        Self::record_output_chunk(
                            &output_buffer,
                            &completion_buffer,
                            &bytes,
                        )
                        .await;
                        let _ = output_tx.send(bytes);
'''
assert process.count(producer_old) == 2, f"exec producer writes: {process.count(producer_old)}"
process = process.replace(producer_old, producer_new)

local_start = process.index("    fn spawn_local_output_task(\n")
local_end = process.index("\n    fn signal_exit", local_start)
local_new = '''    fn spawn_local_output_task(
        mut stdout_receiver: tokio::sync::mpsc::Receiver<Vec<u8>>,
        mut stderr_receiver: tokio::sync::mpsc::Receiver<Vec<u8>>,
        output_handles: OutputHandles,
        output_tx: broadcast::Sender<Vec<u8>>,
    ) -> JoinHandle<()> {
        let OutputHandles {
            output_buffer,
            completion_buffer,
            output_notify,
            output_closed,
            output_closed_notify,
            ..
        } = output_handles;
        tokio::spawn(async move {
            let _output_task_guard = OutputTaskGuard {
                output_closed: Arc::clone(&output_closed),
                output_closed_notify: Arc::clone(&output_closed_notify),
            };
            let mut stdout_open = true;
            let mut stderr_open = true;
            while stdout_open || stderr_open {
                let chunk = tokio::select! {
                    stdout = stdout_receiver.recv(), if stdout_open => match stdout {
                        Some(chunk) => Some(chunk),
                        None => {
                            stdout_open = false;
                            None
                        }
                    },
                    stderr = stderr_receiver.recv(), if stderr_open => match stderr {
                        Some(chunk) => Some(chunk),
                        None => {
                            stderr_open = false;
                            None
                        }
                    },
                };
                let Some(chunk) = chunk else {
                    continue;
                };
                Self::record_output_chunk(&output_buffer, &completion_buffer, &chunk).await;
                let _ = output_tx.send(chunk);
                output_notify.notify_waiters();
            }
        })
    }
'''
process = process[:local_start] + local_new + process[local_end:]
write(process_path, process)


watcher_path = "codex-rs/core/src/unified_exec/async_watcher.rs"
watcher = read(watcher_path)
watcher = replace_once(
    watcher,
    "use super::UnifiedExecContext;\n",
    "use super::UnifiedExecContext;\nuse super::process::OutputBuffer;\n",
    "watcher output buffer import",
)
watcher = replace_once(
    watcher,
    "    let mut receiver = process.output_receiver();\n    let output_drained = process.output_drained_notify();\n",
    "    let mut receiver = process.output_receiver();\n    let completion_buffer = process.completion_buffer();\n    let output_drained = process.output_drained_notify();\n",
    "watcher completion capture",
)
call_arg = "                        &mut pending,\n                        &transcript,\n                        &call_id,\n"
assert watcher.count(call_arg) == 2, f"process_chunk transcript calls: {watcher.count(call_arg)}"
watcher = watcher.replace(call_arg, "                        &mut pending,\n                        &call_id,\n")
watcher = replace_once(
    watcher,
    "        output_drained.notify_one();\n",
    "        reconcile_transcript(&transcript, &completion_buffer).await;\n        output_drained.notify_one();\n",
    "completion reconciliation",
)
process_marker = "async fn process_chunk(\n"
assert watcher.count(process_marker) == 1, "process_chunk marker"
reconcile = '''async fn reconcile_transcript(
    transcript: &Arc<Mutex<HeadTailBuffer>>,
    completion_buffer: &OutputBuffer,
) {
    let authoritative = completion_buffer.lock().await.drain();
    *transcript.lock().await = authoritative;
}

'''
watcher = watcher.replace(process_marker, reconcile + process_marker, 1)
watcher = replace_once(
    watcher,
    '''async fn process_chunk(
    pending: &mut VecDeque<u8>,
    transcript: &Arc<Mutex<HeadTailBuffer>>,
    call_id: &str,
''',
    '''async fn process_chunk(
    pending: &mut VecDeque<u8>,
    call_id: &str,
''',
    "process_chunk signature",
)
watcher = replace_once(
    watcher,
    '''    while let Some(prefix) = split_valid_utf8_prefix(pending) {
        {
            let mut guard = transcript.lock().await;
            guard.push_chunk(prefix.to_vec());
        }

        if *emitted_deltas >= MAX_EXEC_OUTPUT_DELTAS_PER_CALL {
''',
    '''    while let Some(prefix) = split_valid_utf8_prefix(pending) {
        if *emitted_deltas >= MAX_EXEC_OUTPUT_DELTAS_PER_CALL {
''',
    "remove subscriber transcript authority",
)
write(watcher_path, watcher)


process_tests_path = "codex-rs/core/src/unified_exec/process_tests.rs"
process_tests = read(process_tests_path)
process_tests = replace_once(
    process_tests,
    "use super::process::UnifiedExecProcess;\n",
    "use super::process::NoopSpawnLifecycle;\nuse super::process::UnifiedExecProcess;\n",
    "process test lifecycle import",
)
process_tests = replace_once(
    process_tests,
    "use codex_exec_server::WriteStatus;\n",
    "use codex_exec_server::WriteStatus;\nuse codex_utils_pty::ProcessDriver;\nuse codex_utils_pty::spawn_from_driver;\n",
    "process test pty imports",
)
process_tests = replace_once(
    process_tests,
    "use std::sync::Arc;\n",
    "use std::sync::Arc;\nuse std::sync::atomic::Ordering;\nuse std::time::Duration;\n",
    "process test std imports",
)
process_tests = replace_once(
    process_tests,
    "use tokio::sync::Mutex;\nuse tokio::sync::watch;\n",
    "use tokio::sync::Mutex;\nuse tokio::sync::broadcast;\nuse tokio::sync::mpsc;\nuse tokio::sync::oneshot;\nuse tokio::sync::watch;\n",
    "process test tokio imports",
)
process_tests += r'''

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
        #[cfg(windows)]
        tty: false,
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
    assert_eq!(
        process.output_handles().output_buffer.lock().await.total_bytes(),
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
'''
write(process_tests_path, process_tests)


watcher_tests_path = "codex-rs/core/src/unified_exec/async_watcher_tests.rs"
watcher_tests = read(watcher_tests_path)
watcher_tests = replace_once(
    watcher_tests,
    "use super::TRAILING_OUTPUT_GRACE;\n",
    "use super::TRAILING_OUTPUT_GRACE;\nuse super::reconcile_transcript;\n",
    "watcher test reconcile import",
)
watcher_tests = replace_once(
    watcher_tests,
    "async fn streaming_output_harness() -> anyhow::Result<StreamingOutputHarness> {\n",
    "async fn unstarted_streaming_output_harness() -> anyhow::Result<StreamingOutputHarness> {\n",
    "unstarted harness rename",
)
watcher_tests = replace_once(
    watcher_tests,
    '''    let transcript = Arc::new(tokio::sync::Mutex::new(HeadTailBuffer::default()));
    start_streaming_output(&process, &context, Arc::clone(&transcript));

    Ok(StreamingOutputHarness {
''',
    '''    let transcript = Arc::new(tokio::sync::Mutex::new(HeadTailBuffer::default()));

    Ok(StreamingOutputHarness {
''',
    "defer streaming subscription",
)
first_test = "#[tokio::test]\nasync fn streaming_output_finishes_on_close_without_waiting_for_grace()"
assert watcher_tests.count(first_test) == 1, "watcher first test marker"
new_tests = r'''async fn streaming_output_harness() -> anyhow::Result<StreamingOutputHarness> {
    let harness = unstarted_streaming_output_harness().await?;
    start_streaming_output(
        &harness.process,
        &harness.context,
        Arc::clone(&harness.transcript),
    );
    Ok(harness)
}

#[tokio::test]
async fn completed_item_includes_output_emitted_before_subscription() -> anyhow::Result<()> {
    let StreamingOutputHarness {
        process,
        stdout_tx,
        exit_tx,
        transcript,
        context,
        rx_event,
    } = unstarted_streaming_output_harness().await?;
    let expected = b"EARLY-OUTPUT-MARKER".to_vec();
    stdout_tx.send(expected.clone()).expect("send early output");

    let output_buffer = Arc::clone(&process.output_handles().output_buffer);
    tokio::time::timeout(Duration::from_secs(1), async {
        loop {
            if output_buffer.lock().await.total_bytes() == expected.len() {
                break;
            }
            tokio::task::yield_now().await;
        }
    })
    .await?;

    start_streaming_output(&process, &context, Arc::clone(&transcript));
    #[allow(deprecated)]
    let cwd = context.step_context.turn.cwd.clone().into();
    spawn_exit_watcher(
        Arc::clone(&process),
        Arc::clone(&context.session),
        Arc::clone(&context.step_context.turn),
        context.call_id,
        vec!["proof".to_string()],
        cwd,
        /*process_id*/ 123,
        /*plugin_attribution*/ None,
        transcript,
        Instant::now(),
        /*network_denial_monitor*/ None,
    );
    exit_tx.send(0).expect("send exit");
    drop(stdout_tx);

    let event = rx_event.recv().await.expect("command end event");
    let EventMsg::ItemCompleted(completed) = event.msg else {
        panic!("expected ItemCompleted");
    };
    let TurnItem::CommandExecution(item) = completed.item else {
        panic!("expected CommandExecution");
    };
    assert_eq!(
        (
            item.status,
            item.exit_code,
            item.aggregated_output.as_deref()
        ),
        (
            CommandExecutionStatus::Completed,
            Some(0),
            Some("EARLY-OUTPUT-MARKER")
        )
    );
    Ok(())
}

#[tokio::test]
async fn reconcile_transcript_replaces_partial_stream_with_authoritative_output() {
    let StreamingOutputHarness { process, .. } = unstarted_streaming_output_harness()
        .await
        .expect("create output harness");
    let transcript = Arc::new(tokio::sync::Mutex::new(HeadTailBuffer::default()));
    let completion_buffer = process.completion_buffer();

    for index in 0..128 {
        let chunk = format!("chunk-{index:04}\n").into_bytes();
        completion_buffer.lock().await.push_chunk(chunk.clone());
        if index >= 64 {
            transcript.lock().await.push_chunk(chunk);
        }
    }
    let expected = completion_buffer
        .lock()
        .await
        .to_bytes_with_omission_marker();

    reconcile_transcript(&transcript, &completion_buffer).await;
    let actual = transcript.lock().await.to_bytes_with_omission_marker();
    assert_eq!(actual, expected);
    assert_eq!(completion_buffer.lock().await.total_bytes(), 0);
}

'''
watcher_tests = watcher_tests.replace(first_test, new_tests + first_test, 1)
write(watcher_tests_path, watcher_tests)
