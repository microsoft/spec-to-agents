from agent_framework import WorkflowBuilder, executor, WorkflowContext


@executor(id="upper_case")
async def to_upper(text: str, ctx: WorkflowContext[str]):
    await ctx.send_message(text.upper())


@executor(id="reverse")
async def to_reverse(text: str, ctx: WorkflowContext[str]):
    await ctx.yield_output(text[::-1])  # type: ignore


event_planner_workflow = (
    WorkflowBuilder(name="event_planner_workflow")
    .set_start_executor(to_upper)
    .add_edge(to_upper, to_reverse)
).build()
