# Learning API Development - Codex Guidance

## Learning Progression System

This directory implements the core learning progression system for the Microsoft Agent Framework reference implementation. The system is designed as a structured educational experience with 6 progressive levels of complexity.

## Learning Level Architecture

### Level 1: Basic Agents (`basic_agents/`)
**Objective**: Understanding fundamental agent creation and interaction patterns

**Key Concepts**:
- Single agent conversations
- Instruction-based agent configuration
- Basic prompt engineering
- Agent response patterns

**Implementation Patterns**:
- Use `PlaceholderAgent` class for development
- Implement instruction sets for different difficulty levels
- Focus on single agent interaction flows
- Include learning notes explaining agent concepts

**Example Endpoints**:
- `/simple_chat` - Basic agent conversation
- `/with_instructions` - Instruction-based agent configuration
- `/agent_types` - Different agent specialization types

### Level 2: Agent Tools (`agent_tools/`)
**Objective**: Understanding agent tool integration and capabilities

**Key Concepts**:
- Python function tools
- MCP (Model Context Protocol) integration
- Hosted Code Interpreter usage
- Tool registration and execution

**Implementation Patterns**:
- Define tool schemas and capabilities
- Implement tool execution logic
- Plan for MCP integration
- Include tool usage examples

**Example Endpoints**:
- `/native_tools` - Python function tools
- `/mcp_integration` - MCP protocol integration
- `/hosted_tools` - Code interpreter tools

### Level 3: Multi-Agent (`multi_agent/`)
**Objective**: Understanding agent collaboration and coordination

**Key Concepts**:
- Agent-to-agent communication
- Task distribution and specialization
- Coordination patterns
- Consensus building

**Implementation Patterns**:
- Implement agent interaction workflows
- Design task delegation strategies
- Create collaboration scenarios
- Include coordination examples

**Example Endpoints**:
- `/simple_collaboration` - Basic agent cooperation
- `/group_discussion` - Multi-agent discussions
- `/task_delegation` - Work distribution patterns

### Level 4: Workflows (`workflows/`)
**Objective**: Understanding workflow orchestration patterns

**Key Concepts**:
- Sequential workflow execution
- Parallel task processing
- Conditional workflow logic
- Error handling in workflows

**Implementation Patterns**:
- Design workflow state machines
- Implement parallel execution patterns
- Create conditional branching logic
- Include workflow monitoring

**Example Endpoints**:
- `/sequential` - Step-by-step workflows
- `/parallel` - Concurrent task execution
- `/conditional` - Decision-based workflows

### Level 5: Orchestration (`orchestration/`)
**Objective**: Understanding advanced coordination patterns

**Key Concepts**:
- Magnetic coordination patterns
- Adaptive agent coordination
- Complex workflow orchestration
- Dynamic resource allocation

**Implementation Patterns**:
- Implement adaptive coordination algorithms
- Design magnetic attraction patterns
- Create dynamic workflow adaptation
- Include orchestration monitoring

**Example Endpoints**:
- `/magnetic_patterns` - Attraction-based coordination
- `/adaptive_coordination` - Dynamic coordination
- `/complex_orchestration` - Advanced workflows

### Level 6: Human-in-the-Loop (`human_loop/`)
**Objective**: Understanding human-AI collaboration patterns

**Key Concepts**:
- Human approval workflows
- Feedback integration
- Intervention mechanisms
- Human-AI coordination

**Implementation Patterns**:
- Design approval request flows
- Implement feedback collection
- Create intervention triggers
- Include human interaction patterns

**Example Endpoints**:
- `/approval_workflows` - Human approval processes
- `/feedback_integration` - Feedback collection
- `/intervention_mechanisms` - Human intervention

## Implementation Guidelines

### Router Structure
Each learning level should have its own router with:
- Clear endpoint naming conventions
- Consistent response formats
- Proper error handling
- Learning progression context

### Response Models
Use Pydantic models for all responses:
```python
class LearningResponse(BaseModel):
    level: int
    concept: str
    description: str
    examples: List[str]
    next_steps: List[str]
    difficulty: DifficultyLevel
```

### Learning Notes Integration
Every endpoint should include:
- **Concept Explanation**: What the user is learning
- **Progressive Context**: How it builds on previous levels
- **Practical Examples**: Real-world usage scenarios
- **Next Steps**: What to explore next

### Agent Integration
- Use placeholder agents during development
- Plan for Agent Framework integration
- Implement instruction-based configuration
- Support multiple difficulty levels

## Development Workflow

### Adding New Learning Endpoints
1. **Identify Level**: Determine appropriate learning level
2. **Design Concept**: Define what users will learn
3. **Implement Endpoint**: Create router and logic
4. **Add Learning Content**: Include educational materials
5. **Update Overview**: Add to learning progression overview

### Testing Strategy
- **Unit Tests**: Test individual endpoint logic
- **Integration Tests**: Test learning progression flow
- **Learning Tests**: Ensure educational content works
- **Progression Tests**: Verify level progression logic

### Documentation Requirements
- **API Documentation**: Use FastAPI automatic generation
- **Learning Notes**: Include educational context
- **Code Examples**: Provide practical implementation examples
- **Progression Guide**: Explain learning path connections

## Common Patterns

### Difficulty Level Support
Implement three difficulty levels for each concept:
- **Beginner**: Basic understanding and simple examples
- **Intermediate**: Practical application and detailed scenarios
- **Advanced**: Complex patterns and optimization strategies

### Error Handling
- **Learning Context**: Provide educational error messages
- **Progression Guidance**: Suggest alternative learning paths
- **Debugging Help**: Include troubleshooting information

### Monitoring Integration
- **Learning Metrics**: Track user progression through levels
- **Concept Mastery**: Monitor understanding of key concepts
- **Performance Metrics**: Track endpoint usage and response times

## Codex Development Focus

When implementing learning endpoints:
- **Educational Value**: Every endpoint should teach something valuable
- **Progressive Complexity**: Build complexity gradually across levels
- **Practical Application**: Include real-world usage examples
- **Agent Integration**: Design around agent capabilities and interactions
- **Learning Progression**: Ensure smooth transitions between levels
- **Production Quality**: Implement proper error handling and monitoring

## Example Implementation Structure

```python
@router.post("/concept_example", response_model=LearningResponse)
async def demonstrate_concept(
    request: ConceptRequest,
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
) -> LearningResponse:
    """
    Demonstrate [CONCEPT] with progressive complexity.
    
    This endpoint teaches users about [CONCEPT] through practical examples.
    The difficulty level determines the complexity of the demonstration.
    """
    # Implementation logic here
    # Include learning notes and progression context
    pass
```

## Next Steps for Development

1. **Complete Basic Agents**: Implement all Level 1 endpoints
2. **Add Agent Tools**: Develop Level 2 tool integration
3. **Implement Multi-Agent**: Create Level 3 collaboration patterns
4. **Design Workflows**: Build Level 4 workflow system
5. **Advanced Orchestration**: Implement Level 5 coordination
6. **Human Integration**: Add Level 6 human-in-the-loop features
