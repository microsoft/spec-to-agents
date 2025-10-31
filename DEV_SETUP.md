# Development Setup Instructions

## Prerequisites

```bash
git submodule update --init --recursive

GIT_LFS_SKIP_SMUDGE=1 uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

# Backend

## Configuration

Add a `.env` file in the root directory with the necessary environment variables for AI Foundry. You can use the `.env.example` file as a template.

## Running the Workflow

### Interactive CLI Mode (Recommended)

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
> Plan a corporate holiday party for 50 people with a budget of $5000

[Workflow executes...]

🤔 VENUE needs your input:
   Which venue do you prefer? (A/B/C)
   Your response > B

[Workflow continues...]

✓ FINAL EVENT PLAN
[Comprehensive plan output]
```

### DevUI Mode

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
- Catering requirements: Coffee breaks mornign and afternoon. Lunch. Options for vegan attendees.
- Logistics: Excellent internet, breakout rooms, good selection of hotels in the locality
```