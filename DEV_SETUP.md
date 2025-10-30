# Development Setup Instructions

## Prerequisites

```bash
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

# Backend

## Configuration

Add a `.env` file in the `src/spec_to_agents/agents` directory with the necessary environment variables for AI Foundry. You can use the `.env.example` file as a template.

## Starting DevUI

Visualize and interact with the agents using DevUI:

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