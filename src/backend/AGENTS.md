# Backend Application Development - Codex Guidance

## FastAPI Application Architecture

This directory contains the main FastAPI application that implements the Microsoft Agent Framework reference system. The application is structured around a learning progression system with 6 levels of complexity.

## Application Structure

### Main Application (`app/main.py`)
- **Lifespan Management**: Proper startup/shutdown with async context manager
- **Service Initialization**: CosmosDB, Redis, monitoring setup
- **Middleware Configuration**: CORS, trusted hosts, request logging
- **API Router Integration**: Learning progression endpoints by level

### Core Components (`app/core/`)
- **Configuration**: Environment-based settings management
- **Models**: Pydantic models for data validation
- **Exceptions**: Custom exception classes and handlers
- **Monitoring**: Metrics collection and observability

### API Structure (`app/api/v1/`)
The API is organized by learning progression levels:

#### Level 1: Basic Agents (`/learning/basic_agents/`)
- Simple agent conversations
- Instruction-based agent configuration
- Single agent interaction patterns

#### Level 2: Agent Tools (`/learning/agent_tools/`)
- Python function tools
- MCP (Model Context Protocol) integration
- Hosted Code Interpreter usage

#### Level 3: Multi-Agent (`/learning/multi_agent/`)
- Agent collaboration patterns
- Group discussion workflows
- Task delegation strategies

#### Level 4: Workflows (`/learning/workflows/`)
- Sequential workflow execution
- Parallel task processing
- Conditional workflow logic

#### Level 5: Orchestration (`/learning/orchestration/`)
- Magnetic coordination patterns
- Adaptive agent coordination
- Complex workflow orchestration

#### Level 6: Human-in-the-Loop (`/learning/human_loop/`)
- Human approval workflows
- Feedback integration
- Intervention mechanisms

## Development Patterns

### Adding New Learning Endpoints
1. **Follow Level Structure**: Place endpoints in appropriate learning level router
2. **Educational Content**: Include learning notes and progression context
3. **Agent Integration**: Use placeholder agents until framework is available
4. **Consistent Response Format**: Use Pydantic models for all responses

### Service Integration
- **Database Services**: Use CosmosService and RedisService from app state
- **Monitoring**: Integrate with MetricsCollector for observability
- **Error Handling**: Use custom exception classes and proper HTTP status codes

### Agent Implementation
- **Placeholder Pattern**: Use `PlaceholderAgent` class during development
- **Instruction-Based**: Configure agents with detailed instruction sets
- **Difficulty Levels**: Support Beginner, Intermediate, Advanced complexity
- **Tool Integration**: Plan for future MCP and native tool support

## Key Implementation Details

### Request Lifecycle
1. **Middleware Processing**: CORS, trusted hosts, logging
2. **Request Logging**: Structured logging with timing and metrics
3. **Router Dispatch**: Learning level specific endpoint handling
4. **Response Processing**: Consistent error handling and logging

### Service State Management
- **Application State**: Services stored in `app.state` for global access
- **Async Initialization**: Proper async service setup in lifespan
- **Resource Cleanup**: Graceful shutdown with service cleanup

### Error Handling Strategy
- **Custom Exceptions**: Domain-specific exception classes
- **Structured Logging**: Consistent error logging with context
- **HTTP Status Codes**: Proper status code mapping
- **User-Friendly Messages**: Educational error responses

## Testing Strategy

### Test Organization
- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test API endpoints and service interactions
- **Learning Tests**: Ensure educational examples work correctly

### Test Patterns
- **Async Testing**: Use pytest-asyncio for async function testing
- **Service Mocking**: Mock external services for isolated testing
- **Response Validation**: Validate Pydantic model responses
- **Error Scenario Testing**: Test exception handling paths

## Configuration Management

### Environment Variables
- **Development**: Use `.env` files for local development
- **Production**: Azure Key Vault integration for secrets
- **Validation**: Pydantic settings with validation

### Service Configuration
- **Azure Services**: Connection strings and credentials
- **OpenAI Integration**: API keys and model configurations
- **Monitoring**: Metrics and logging configuration

## Performance Considerations

### Async Patterns
- **I/O Operations**: Use async for database and external API calls
- **Concurrent Processing**: Leverage FastAPI's async capabilities
- **Resource Management**: Proper connection pooling and cleanup

### Caching Strategy
- **Redis Integration**: Session and result caching
- **Response Caching**: Cache frequently accessed data
- **Invalidation**: Smart cache invalidation strategies

## Security Implementation

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access**: Learning level appropriate access control
- **Input Validation**: Pydantic model validation for all inputs

### Azure Security
- **Managed Identity**: Use Azure managed identities where possible
- **Key Vault**: Secure storage of secrets and credentials
- **Network Security**: Proper network isolation and firewall rules

## Monitoring & Observability

### Metrics Collection
- **Request Metrics**: Timing, status codes, endpoint usage
- **Business Metrics**: Learning progression, agent interactions
- **Infrastructure Metrics**: Service health, resource usage

### Logging Strategy
- **Structured Logging**: JSON-formatted logs with context
- **Log Levels**: Appropriate log level usage
- **Correlation IDs**: Request tracing across services

## Development Workflow

### Code Quality
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Clear docstrings and comments
- **Error Handling**: Proper exception handling patterns
- **Testing**: Comprehensive test coverage

### Deployment Considerations
- **Containerization**: Docker support for deployment
- **Environment Management**: Proper environment configuration
- **Health Checks**: Application health monitoring
- **Graceful Shutdown**: Proper resource cleanup

## Common Development Tasks

### Adding New Agents
1. Create agent class in `app/agents/specialists/`
2. Implement instruction sets for different difficulty levels
3. Add to appropriate learning level endpoints
4. Include comprehensive testing

### Extending Learning Levels
1. Add new router in `app/api/v1/learning/`
2. Implement progressive complexity
3. Update main router integration
4. Add to learning overview endpoint

### Service Integration
1. Implement service class in `app/services/`
2. Add to application lifespan
3. Integrate with monitoring and logging
4. Add proper error handling

## Codex Development Focus

When working on backend features:
- **Maintain Learning Structure**: All features should fit the 6-level progression
- **Agent-Centric Design**: Design around agent capabilities and interactions
- **Production Quality**: Implement proper monitoring, caching, and error handling
- **Educational Value**: Include learning notes and progressive complexity
- **Azure Integration**: Follow Azure best practices for services and security
