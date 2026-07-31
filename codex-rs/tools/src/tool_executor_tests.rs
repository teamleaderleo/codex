use super::ToolExecutor;
use super::ToolExecutorFuture;
use crate::JsonSchema;
use crate::ToolName;
use crate::ToolOperationEffect;
use crate::ToolSpec;

struct ConservativeExecutor;

impl ToolExecutor<()> for ConservativeExecutor {
    fn tool_name(&self) -> ToolName {
        ToolName::plain("conservative")
    }

    fn spec(&self) -> ToolSpec {
        test_spec("conservative")
    }

    fn handle(&self, _invocation: ()) -> ToolExecutorFuture<'_> {
        Box::pin(async { panic!("test executor should not be invoked") })
    }
}

struct ReadOnlyExecutor;

impl ToolExecutor<()> for ReadOnlyExecutor {
    fn tool_name(&self) -> ToolName {
        ToolName::plain("read_only")
    }

    fn spec(&self) -> ToolSpec {
        test_spec("read_only")
    }

    fn operation_effect(&self) -> ToolOperationEffect {
        ToolOperationEffect::ReadOnly
    }

    fn handle(&self, _invocation: ()) -> ToolExecutorFuture<'_> {
        Box::pin(async { panic!("test executor should not be invoked") })
    }
}

#[test]
fn unclassified_executor_is_potentially_mutating() {
    assert_eq!(
        ConservativeExecutor.operation_effect(),
        ToolOperationEffect::PotentialMutation
    );
}

#[test]
fn executor_can_declare_read_only_effect() {
    assert_eq!(
        ReadOnlyExecutor.operation_effect(),
        ToolOperationEffect::ReadOnly
    );
}

fn test_spec(name: &str) -> ToolSpec {
    ToolSpec::ToolSearch {
        execution: "client".to_string(),
        description: name.to_string(),
        parameters: JsonSchema::default(),
    }
}
