use std::future::pending;
use std::sync::Arc;
use std::sync::Mutex;
use std::time::Duration;

use crate::function_tool::FunctionCallError;
use crate::session::step_context::StepContext;
use crate::tools::context::FunctionToolOutput;
use crate::tools::context::ToolInvocation;
use crate::tools::context::ToolPayload;
use crate::tools::parallel::ToolCallRuntime;
use crate::tools::registry::CoreToolRuntime;
use crate::tools::registry::ToolExecutor;
use crate::tools::registry::ToolRegistry;
use crate::tools::router::ToolCall;
use crate::tools::router::ToolRouter;
use crate::turn_diff_tracker::TurnDiffTracker;
use tokio::sync::oneshot;
use tokio_util::sync::CancellationToken;

struct NonSettlingCancellationHandler {
    tool_name: codex_tools::ToolName,
    started: Mutex<Option<oneshot::Sender<()>>>,
    cleanup_started: Mutex<Option<oneshot::Sender<()>>>,
}

impl ToolExecutor<ToolInvocation> for NonSettlingCancellationHandler {
    fn tool_name(&self) -> codex_tools::ToolName {
        self.tool_name.clone()
    }

    fn spec(&self) -> codex_tools::ToolSpec {
        codex_tools::ToolSpec::Function(codex_tools::ResponsesApiTool {
            name: self.tool_name.name.clone(),
            description: "Non-settling cancellation test tool.".to_string(),
            strict: false,
            defer_loading: None,
            parameters: codex_tools::JsonSchema::default(),
            output_schema: None,
        })
    }

    fn handle(&self, invocation: ToolInvocation) -> codex_tools::ToolExecutorFuture<'_> {
        Box::pin(self.handle_call(invocation))
    }
}

impl NonSettlingCancellationHandler {
    async fn handle_call(
        &self,
        invocation: ToolInvocation,
    ) -> Result<Box<dyn crate::tools::context::ToolOutput>, FunctionCallError> {
        let started = self
            .started
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner)
            .take();
        if let Some(started) = started {
            let _ = started.send(());
        }

        invocation.cancellation_token.cancelled().await;

        let cleanup_started = self
            .cleanup_started
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner)
            .take();
        if let Some(cleanup_started) = cleanup_started {
            let _ = cleanup_started.send(());
        }

        pending::<Result<Box<dyn crate::tools::context::ToolOutput>, FunctionCallError>>().await
    }
}

impl CoreToolRuntime for NonSettlingCancellationHandler {
    fn waits_for_runtime_cancellation(&self) -> bool {
        true
    }
}

#[tokio::test]
async fn cancellation_waiting_for_nonsettling_runtime_cleanup_has_no_terminal_receipt()
-> anyhow::Result<()> {
    let (session, turn_context) = crate::session::tests::make_session_and_context().await;
    let session = Arc::new(session);
    let turn_context = Arc::new(turn_context);
    let tool_name = codex_tools::ToolName::plain("nonsettling_cleanup_tool");
    let (started_tx, started_rx) = oneshot::channel();
    let (cleanup_started_tx, cleanup_started_rx) = oneshot::channel();
    let handler = Arc::new(NonSettlingCancellationHandler {
        tool_name: tool_name.clone(),
        started: Mutex::new(Some(started_tx)),
        cleanup_started: Mutex::new(Some(cleanup_started_tx)),
    }) as Arc<dyn CoreToolRuntime>;
    let step_context = StepContext::for_test(Arc::clone(&turn_context));
    let router = Arc::new(ToolRouter::from_parts(
        ToolRegistry::from_tools([handler]),
        Vec::new(),
    ));
    let tracker = Arc::new(tokio::sync::Mutex::new(TurnDiffTracker::new()));
    let runtime = ToolCallRuntime::new(router, session, step_context, tracker);
    let cancellation_token = CancellationToken::new();
    let call = ToolCall {
        tool_name,
        call_id: "call-1".to_string(),
        payload: ToolPayload::Function {
            arguments: "{}".to_string(),
        },
        encrypted_function_args: None,
    };

    let mut response_task =
        tokio::spawn(runtime.handle_tool_call(call, cancellation_token.clone()));
    started_rx.await.expect("handler should start");
    cancellation_token.cancel();
    cleanup_started_rx
        .await
        .expect("handler should begin cancellation cleanup");

    let pending_result = tokio::time::timeout(Duration::from_millis(100), &mut response_task).await;
    assert!(
        pending_result.is_err(),
        "current runtime should remain pending while opted-in cancellation cleanup never settles"
    );

    response_task.abort();
    let join_error = response_task
        .await
        .expect_err("aborted characterization task should not complete normally");
    assert!(join_error.is_cancelled());

    Ok(())
}
