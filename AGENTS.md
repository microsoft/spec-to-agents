# Microsoft Agent Framework Reference Implementation - Codex Guidance

## Project Overview

This is a **Microsoft Agent Framework Reference Implementation** that serves as an educational platform for learning agent orchestration patterns. The project demonstrates progressive complexity from basic single-agent interactions to advanced multi-agent orchestration workflows.

## Architecture Overview

### Core Components
- **FastAPI Backend**: Modern Python web framework with async support
- **Learning Progression System**: 6 structured levels from beginner to advanced
- **Agent Specialists**: Specialized agents for event planning, venue research, budget analysis
- **Azure Integration**: CosmosDB, Redis, Azure AI Foundry, monitoring
- **Real-time Features**: WebSocket streaming, live workflow monitoring

### Learning Levels (Progressive Complexity)
1. **Level 1**: Basic Agents - Single agent conversations
2. **Level 2**: Agent Tools - Python functions, MCP integration, Code Interpreter
3. **Level 3**: Multi-Agent - Collaboration and task delegation
4. **Level 4**: Workflows - Sequential, parallel, conditional patterns
5. **Level 5**: Orchestration - Magnetic patterns, adaptive coordination
6. **Level 6**: Human-in-the-Loop - Approvals, feedback, interventions

## Development Guidelines

### Code Style & Standards
- **Python 3.13+**: Use modern Python features and type hints
- **Async/Await**: Prefer async patterns for I/O operations
- **Structured Logging**: Use `structlog` for consistent logging
- **Type Safety**: Use Pydantic models and type hints throughout
- **Error Handling**: Implement proper exception handling with custom exception classes

### Project Structure
```
src/backend/
├── app/
│   ├── api/v1/          # REST API endpoints by learning level
│   ├── agents/          # Agent implementations and specialists
│   ├── core/            # Configuration, models, exceptions
│   ├── services/        # Database, monitoring, external services
│   └── tools/           # MCP and native tool integrations
├── tests/               # Unit and integration tests
└── requirements.txt     # Python dependencies
```

### Key Technologies
- **FastAPI**: Web framework with automatic OpenAPI generation
- **Pydantic**: Data validation and settings management
- **Azure SDK**: CosmosDB, Redis, Key Vault, Service Bus
- **OpenAI/Azure OpenAI**: AI model integration
- **uv**: Modern Python package management

## Development Workflow

### Adding New Features
1. **Follow Learning Progression**: New features should fit into the 6-level learning structure
2. **Agent-First Design**: Design around agent capabilities and interactions
3. **Educational Focus**: Include learning notes and code examples
4. **Production Ready**: Implement proper monitoring, caching, and error handling

### Testing Strategy
- **Unit Tests**: Test individual agent behaviors and functions
- **Integration Tests**: Test API endpoints and service interactions
- **Learning Tests**: Ensure educational examples work correctly

### Documentation Requirements
- **Code Comments**: Explain complex logic and agent behaviors
- **API Documentation**: Use FastAPI's automatic OpenAPI generation
- **Learning Notes**: Include educational context for each endpoint

## Common Patterns

### Agent Implementation
- Use placeholder agents during development (see `event_planner.py`)
- Implement proper error handling and logging
- Follow the instruction-based configuration pattern
- Support multiple difficulty levels (Beginner, Intermediate, Advanced)

### API Design
- RESTful endpoints with clear naming conventions
- Consistent response formats using Pydantic models
- Proper HTTP status codes and error handling
- Include learning progression context

### Service Integration
- Async service initialization in application lifespan
- Proper resource cleanup on shutdown
- Structured logging throughout the request lifecycle
- Metrics collection for monitoring

## Current Development Status

- **Framework Integration**: Currently using placeholder agents (Agent Framework not yet available)
- **Learning System**: Core structure implemented, endpoints ready for content
- **Infrastructure**: Azure services configured, monitoring setup
- **Testing**: Basic test structure in place

## Next Steps for Development

1. **Complete Learning Content**: Implement educational examples for each level
2. **Agent Framework Integration**: Replace placeholders when framework is available
3. **Enhanced Monitoring**: Add more detailed metrics and observability
4. **Frontend Development**: Create learning interface for users
5. **Documentation**: Expand API docs and learning materials

## Codex-Specific Guidance

When working on this project:
- **Maintain Educational Focus**: Every feature should teach something about agent orchestration
- **Follow Progressive Complexity**: Build features that fit the 6-level learning structure
- **Use Modern Python**: Leverage Python 3.13+ features and async patterns
- **Azure Integration**: Follow Azure best practices for services and monitoring
- **Agent Patterns**: Design around agent capabilities, interactions, and workflows
