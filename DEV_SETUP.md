# Development Setup Instructions

## Quick Start with Azure Deployment

The recommended way to set up the project is using `azd up`, which will:
1. Create the necessary Azure resources
2. Generate the `.env` file automatically
3. Install all dependencies with `uv sync`

```bash
azd up

# Install pre-commit hooks
uv run pre-commit install
```

## Manual Setup (Alternative)

If you prefer to set up manually or are working without Azure resources:

```bash
# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Configuration

Create a `.env` file in the root directory with the necessary environment variables for AI Foundry. You can use the `.env.example` file as a template.

# Running the Workflow

## Interactive CLI Mode (Recommended)

Run the event planning workflow with human-in-the-loop via command line:

```bash
uv run console
```

This starts an interactive session where you can:
- Enter an event planning request
- Provide feedback when agents need clarification or approval
- See the final synthesized event plan

Example interaction:
```
Enter your event planning request:
> Plan a corporate holiday party for 50 people on 6th December 2025 in Seattle with a budget of $5000

[Workflow executes...]

🤔 VENUE needs your input:
   Which venue do you prefer? (A/B/C)
   Your response > B

[Workflow continues...]

✓ FINAL EVENT PLAN
[Comprehensive plan output]
```

## DevUI Mode

Alternatively, visualize and interact with the agents using DevUI:

```bash
uv run app
```

Provide the following sample input:

```text
Book a conference for AI developers in Florida

- Date: 19-23 January 2026
- Attendees: Aprox. 1000
- Budget: $500K
- Venue: Hotel conference center
- Catering requirements: Coffee breaks morning and afternoon. Lunch. Options for vegan attendees.
- Logistics: Excellent internet, breakout rooms, good selection of hotels in the locality
```

# Debugging the Workflow

## Interactive CLI Mode (Recommended)

The following instructions explain how to debug the interactive console using Visual Studio Code

1. Optionally set a breakpoint where you want execution to stop
    - E.g. you could set a breakpoint at the start of `build_event_planning_workflow` in [core.py](./src/spec_to_agents/workflow/core.py) to step through building the workflow
1. Open the [console.py](./src/spec_to_agents/console.py)
1. Use the Run -> Start Debugging (or press F5)

## DevUI Mode

The following instructions explain how to debug the interactive console using Visual Studio Code

1. Optionally set a breakpoint where you want execution to stop
    - E.g. you could set a breakpoint at the start of `build_event_planning_workflow` in [core.py](./src/spec_to_agents/workflow/core.py) to step through building the workflow
1. Open the [main.py](./src/spec_to_agents/main.py)
1. Use the Run -> Start Debugging (or press F5)

# Running Tests

Run the following command

```bash
uv run pytest
```