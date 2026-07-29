from pathlib import Path


def replace(path: str, old: str, new: str, count: int = 1) -> None:
    file = Path(path)
    text = file.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(
            f"{path}: expected {count} occurrence(s), found {actual}: {old!r}"
        )
    file.write_text(text.replace(old, new))


replace(
    "codex-rs/core/src/unified_exec/head_tail_buffer.rs",
    "#[derive(Debug)]",
    "#[derive(Clone, Debug)]",
)

process = "codex-rs/core/src/unified_exec/process.rs"
replace(
    process,
    "    output_tx: broadcast::Sender<Vec<u8>>,\n    output_buffer: OutputBuffer,",
    "    output_tx: broadcast::Sender<Vec<u8>>,\n    output_buffer: OutputBuffer,\n    completion_buffer: OutputBuffer,",
)
replace(
    process,
    "        let output_buffer = Arc::new(Mutex::new(HeadTailBuffer::default()));\n        let output_notify = Arc::new(Notify::new());",
    "        let output_buffer = Arc::new(Mutex::new(HeadTailBuffer::default()));\n        let completion_buffer = Arc::new(Mutex::new(HeadTailBuffer::default()));\n        let output_notify = Arc::new(Notify::new());",
)
replace(
    process,
    "            output_tx,\n            output_buffer,\n            output_notify,",
    "            output_tx,\n            output_buffer,\n            completion_buffer,\n            output_notify,",
)
replace(
    process,
    "    pub(super) fn output_receiver(&self) -> tokio::sync::broadcast::Receiver<Vec<u8>> {",
    "    pub(super) fn completion_buffer(&self) -> OutputBuffer {\n        Arc::clone(&self.completion_buffer)\n    }\n\n    pub(super) fn output_receiver(&self) -> tokio::sync::broadcast::Receiver<Vec<u8>> {",
)
replace(
    process,
    "            Arc::clone(&managed.output_buffer),\n            Arc::clone(&managed.output_notify),",
    "            Arc::clone(&managed.output_buffer),\n            Arc::clone(&managed.completion_buffer),\n            Arc::clone(&managed.output_notify),",
)
replace(
    process,
    "        managed.output_task = Some(Self::spawn_exec_server_output_task(\n            started,\n            output_handles,\n            managed.output_tx.clone(),",
    "        managed.output_task = Some(Self::spawn_exec_server_output_task(\n            started,\n            output_handles,\n            Arc::clone(&managed.completion_buffer),\n            managed.output_tx.clone(),",
)
replace(
    process,
    "    fn spawn_exec_server_output_task(\n        started: StartedExecProcess,\n        output_handles: OutputHandles,\n        output_tx: broadcast::Sender<Vec<u8>>,",
    "    async fn record_output_chunk(\n        output_buffer: &OutputBuffer,\n        completion_buffer: &OutputBuffer,\n        chunk: &[u8],\n    ) {\n        output_buffer.lock().await.push_chunk(chunk.to_vec());\n        completion_buffer\n            .lock()\n            .await\n            .push_chunk(chunk.to_vec());\n    }\n\n    fn spawn_exec_server_output_task(\n        started: StartedExecProcess,\n        output_handles: OutputHandles,\n        completion_buffer: OutputBuffer,\n        output_tx: broadcast::Sender<Vec<u8>>,",
)
replace(
    process,
    "                        let mut guard = output_buffer.lock().await;\n                        guard.push_chunk(bytes.clone());\n                        drop(guard);\n                        let _ = output_tx.send(bytes);",
    "                        Self::record_output_chunk(\n                            &output_buffer,\n                            &completion_buffer,\n                            &bytes,\n                        )\n                        .await;\n                        let _ = output_tx.send(bytes);",
    count=2,
)
replace(
    process,
    "    fn spawn_local_output_task(\n        mut receiver: tokio::sync::broadcast::Receiver<Vec<u8>>,\n        buffer: OutputBuffer,\n        output_notify: Arc<Notify>,",
    "    fn spawn_local_output_task(\n        mut receiver: tokio::sync::broadcast::Receiver<Vec<u8>>,\n        buffer: OutputBuffer,\n        completion_buffer: OutputBuffer,\n        output_notify: Arc<Notify>,",
)
replace(
    process,
    "                        let mut guard = buffer.lock().await;\n                        guard.push_chunk(chunk.clone());\n                        drop(guard);\n                        let _ = output_tx.send(chunk);",
    "                        Self::record_output_chunk(&buffer, &completion_buffer, &chunk)\n                            .await;\n                        let _ = output_tx.send(chunk);",
)

watcher = "codex-rs/core/src/unified_exec/async_watcher.rs"
replace(
    watcher,
    "/// Spawn a background task that continuously reads from the PTY, appends to the\n/// shared transcript, and emits ExecCommandOutputDelta events on UTF‑8\n/// boundaries.",
    "/// Spawn a background task that emits best-effort ExecCommandOutputDelta events\n/// on UTF-8 boundaries. Before signaling that output is drained, replace the\n/// event-side transcript with the producer-owned authoritative transcript.",
)
replace(
    watcher,
    "    let mut receiver = process.output_receiver();\n    let output_drained = process.output_drained_notify();",
    "    let mut receiver = process.output_receiver();\n    let completion_buffer = process.completion_buffer();\n    let output_drained = process.output_drained_notify();",
)
replace(
    watcher,
    "        }\n        output_drained.notify_one();\n    });\n}",
    "        }\n        reconcile_transcript(&transcript, &completion_buffer).await;\n        output_drained.notify_one();\n    });\n}",
)
replace(
    watcher,
    "async fn process_chunk(\n",
    "async fn reconcile_transcript(\n    transcript: &Arc<Mutex<HeadTailBuffer>>,\n    completion_buffer: &Arc<Mutex<HeadTailBuffer>>,\n) {\n    let authoritative = completion_buffer.lock().await.clone();\n    *transcript.lock().await = authoritative;\n}\n\nasync fn process_chunk(\n",
)
replace(
    watcher,
    "/// Emit an ExecCommandEnd event for a unified exec session, using the transcript\n/// as the primary source of aggregated_output and falling back to the provided\n/// text when the transcript is empty.",
    "/// Emit an ExecCommandEnd event for a unified exec session. A non-empty fallback\n/// is the authoritative output collected by the synchronous command path;\n/// background completions use the reconciled producer-owned transcript.",
)
replace(
    watcher,
    "async fn resolve_aggregated_output(\n    transcript: &Arc<Mutex<HeadTailBuffer>>,\n    fallback: String,\n) -> String {\n    let guard = transcript.lock().await;",
    "async fn resolve_aggregated_output(\n    transcript: &Arc<Mutex<HeadTailBuffer>>,\n    fallback: String,\n) -> String {\n    if !fallback.is_empty() {\n        return fallback;\n    }\n\n    let guard = transcript.lock().await;",
)

tests = "codex-rs/core/src/unified_exec/async_watcher_tests.rs"
replace(
    tests,
    "use super::spawn_exit_watcher;",
    "use super::reconcile_transcript;\nuse super::spawn_exit_watcher;",
)
replace(
    tests,
    "async fn streaming_output_harness() -> anyhow::Result<StreamingOutputHarness> {",
    "async fn unstarted_streaming_output_harness() -> anyhow::Result<StreamingOutputHarness> {",
)
replace(
    tests,
    "    let transcript = Arc::new(tokio::sync::Mutex::new(HeadTailBuffer::default()));\n    start_streaming_output(&process, &context, Arc::clone(&transcript));\n\n    Ok(StreamingOutputHarness {",
    "    let transcript = Arc::new(tokio::sync::Mutex::new(HeadTailBuffer::default()));\n\n    Ok(StreamingOutputHarness {",
)
replace(
    tests,
    "}\n\n#[tokio::test]\nasync fn streaming_output_finishes_on_close_without_waiting_for_grace()",
    """}

async fn streaming_output_harness() -> anyhow::Result<StreamingOutputHarness> {
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

    let output_buffer = process.output_handles().output_buffer;
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
    let cwd = context.turn.cwd.clone().into();
    spawn_exit_watcher(
        Arc::clone(&process),
        Arc::clone(&context.session),
        Arc::clone(&context.turn),
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
        (item.status, item.exit_code, item.aggregated_output.as_deref()),
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
    let transcript = Arc::new(tokio::sync::Mutex::new(HeadTailBuffer::default()));
    let completion_buffer = Arc::new(tokio::sync::Mutex::new(HeadTailBuffer::default()));

    for index in 0..128 {
        let chunk = format!("chunk-{index:04}\n").into_bytes();
        completion_buffer.lock().await.push_chunk(chunk.clone());
        if index >= 64 {
            transcript.lock().await.push_chunk(chunk);
        }
    }

    reconcile_transcript(&transcript, &completion_buffer).await;
    let actual = transcript.lock().await.clone();
    let expected = completion_buffer.lock().await.clone();
    assert_eq!(actual, expected);
}

#[tokio::test]
async fn streaming_output_finishes_on_close_without_waiting_for_grace()""",
)
