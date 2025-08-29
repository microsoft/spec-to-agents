# Spec-to-Agent Backend

FastAPI backend for the Spec-to-Agent sample demonstrating Microsoft Agent Framework through event planning orchestration.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Setup and Run

```bash
# Create virtual environment
uv venv

# Install dependencies
uv sync

# Run the FastAPI server
uv run python app/main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🏗️ Architecture

### Project Structure
```
src/backend/
├── app/
│   ├── agents/          # Agent generation and orchestration
│   ├── api/v1/          # REST API endpoints
│   ├── core/            # Configuration, models, exceptions
│   ├── services/        # Database, monitoring, external services
│   ├── tools/           # MCP and native tool integrations
│   └── main.py          # FastAPI application entry point
├── tests/               # Unit and integration tests
└── pyproject.toml       # Python dependencies and configuration
```

### Core Components
- **FastAPI Application**: Modern async web framework
- **Agent Framework Integration**: Microsoft Agent Framework patterns
- **Event Planning Domain**: Specialized agents for event orchestration
- **Azure Integration**: Azure AI Projects, Azure AI Agents, CosmosDB
- **Real-time Features**: WebSocket support for live agent interactions

## 🤖 Agent Framework Integration

This backend follows Microsoft Agent Framework design principles:

### Tier-based Imports
```python
# Tier 0 (Core)
from agent_framework import Agent, ai_function

# Tier 1 (Advanced)
from agent_framework.workflows import WorkflowBuilder

# Tier 2 (Connectors)
from agent_framework.azure import AzureChatClient
```

### Tool Creation
```python
from typing import Annotated
from agent_framework import ai_function

@ai_function(description="Calculate event budget breakdown")
async def calculate_budget(
    total_budget: Annotated[float, "Total event budget"],
    venue_percentage: Annotated[float, "Percentage for venue"] = 30.0
) -> dict:
    """Calculate event budget breakdown by category."""
    return {
        "venue": total_budget * (venue_percentage / 100),
        "catering": total_budget * 0.25,
        "entertainment": total_budget * 0.15,
        "logistics": total_budget * 0.30
    }
```

### Agent Creation
```python
event_planner = Agent(
    name="EventPlannerAgent",
    model_client=AzureChatClient(),
    tools=[calculate_budget],
    description="Specialized agent for event planning coordination"
)
```

## 🛠️ Development

### Code Quality
```bash
# Lint and format code
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy .
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/unit/test_agents/
```

### Configuration
- Environment variables: Use `.env` file in the backend directory
- Settings: Managed via Pydantic Settings in `app/core/config.py`
- Azure services: Configure connection strings and credentials

## 🎭 Event Planning Sample

### The Scenario
The backend implements a comprehensive event planning system with multiple specialized agents:

- **Event Coordinator**: Orchestrates the overall planning process
- **Venue Specialist**: Researches and recommends venues
- **Budget Analyst**: Manages costs and financial constraints
- **Catering Coordinator**: Handles food and beverage planning
- **Logistics Manager**: Coordinates schedules and resources

### API Endpoints
- `POST /api/v1/agents/generate` - Generate agents from specifications
- `POST /api/v1/orchestration/group-chat` - Start group chat coordination
- `GET /api/v1/workflows/status/{workflow_id}` - Monitor workflow progress
- `WebSocket /ws/workflow/{workflow_id}` - Real-time workflow updates

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Application
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Azure AI
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_API_KEY=your-key

# Database
COSMOS_ENDPOINT=your-cosmos-endpoint
```

### Optional Dependencies
```bash
# Install with agent framework (when available)
uv sync --extra agent-framework

# Install with development tools
uv sync --extra dev
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the `src/backend` directory
2. **Agent Framework Missing**: The app uses fallback implementations when the framework isn't available
3. **Azure Credentials**: Check your Azure configuration and credentials
4. **Port Conflicts**: Change the port in `.env` if 8000 is already in use

### Logs
The application uses structured logging. Check the console output for detailed information about agent interactions and API requests.

## 📚 Learn More

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/azure/ai-services/agent-framework/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure AI Services](https://azure.microsoft.com/products/ai-services/)

---

**Part of the Spec-to-Agent sample** - demonstrating Microsoft Agent Framework through event planning orchestration.
