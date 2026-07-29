use super::ToolExecutor;
use super::ToolExecutorFuture;
use crate::ToolName;
use crate::ToolOperationEffect;
use crate::ToolSpec;

struct UnclassifiedRuntime;

impl ToolExecutor<()> for UnclassifiedRuntime {
    fn tool_name(&self) -> ToolName {
        panic!("tool_name is not used by this contract test")
    }

    fn spec(&self) -> ToolSpec {
        panic!("spec is not used by this contract test")
    }

    fn handle(&self, _invocation: ()) -> ToolExecutorFuture<'_> {
        Box::pin(async { panic!("handle is not used by this contract test") })
    }
}

#[test]
fn unclassified_runtime_defaults_to_potential_mutation() {
    assert_eq!(
        UnclassifiedRuntime.operation_effect(),
        ToolOperationEffect::PotentialMutation
    );
}
