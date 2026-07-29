from pathlib import Path

path = Path('.github/fieldwork/83_typed_operation_identity.py')
text = path.read_text(encoding='utf-8')

replacements = {
    """    dedent(
        '''\\
                        .begin_tool_operation_receipt(
                            call_id_owned.clone(),
                            ToolOperationEffect::PotentialMutation,
                        )
        '''
    ),
""": """    \"                    .begin_tool_operation_receipt(\\n                        call_id_owned.clone(),\\n                        ToolOperationEffect::PotentialMutation,\\n                    )\\n\",
""",
    """    dedent(
        '''\\
                        .begin_tool_operation_receipt_for_id(
                            operation_id.clone(),
                            ToolOperationEffect::PotentialMutation,
                        )
        '''
    ),
""": """    \"                    .begin_tool_operation_receipt_for_id(\\n                        operation_id.clone(),\\n                        ToolOperationEffect::PotentialMutation,\\n                    )\\n\",
""",
    """    dedent(
        '''\\
            invocation
                .session
                .record_tool_operation_terminal(&invocation.call_id, terminal_state)
                .await;
        '''
    ),
""": """    \"    invocation\\n        .session\\n        .record_tool_operation_terminal(&invocation.call_id, terminal_state)\\n        .await;\\n\",
""",
    """    dedent(
        '''\\
            let operation_id = invocation.operation_id();
            invocation
                .session
                .record_tool_operation_terminal_for_id(&operation_id, terminal_state)
                .await;
        '''
    ),
""": """    \"    let operation_id = invocation.operation_id();\\n    invocation\\n        .session\\n        .record_tool_operation_terminal_for_id(&operation_id, terminal_state)\\n        .await;\\n\",
""",
    """    dedent(
        '''\\
            session
                .record_tool_operation_terminal(call_id, receipt_terminal_state(outcome))
                .await;
        '''
    ),
""": """    \"    session\\n        .record_tool_operation_terminal(call_id, receipt_terminal_state(outcome))\\n        .await;\\n\",
""",
    """    dedent(
        '''\\
            let operation_id = source.operation_id(call_id);
            session
                .record_tool_operation_terminal_for_id(
                    &operation_id,
                    receipt_terminal_state(outcome),
                )
                .await;
        '''
    ),
""": """    \"    let operation_id = source.operation_id(call_id);\\n    session\\n        .record_tool_operation_terminal_for_id(\\n            &operation_id,\\n            receipt_terminal_state(outcome),\\n        )\\n        .await;\\n\",
""",
}

for old, new in replacements.items():
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'generator anchor mismatch: expected one, found {count}: {old[:80]!r}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
