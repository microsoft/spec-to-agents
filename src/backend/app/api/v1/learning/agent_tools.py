"""
Level 2: Agent Tools API

This module implements the second learning level focusing on agent tool integration.
Users learn to enhance agents with Python functions, MCP tools, and hosted capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Annotated
import structlog
import asyncio
import math
from datetime import datetime

# Microsoft Agent Framework imports
try:
    from agent_framework import ChatClientAgent, ai_function
    from agent_framework.azure import AzureChatClient
    from agent_framework.hosted import HostedCodeInterpreterTool
except ImportError:
    # Fallback for development/testing
    def ai_function(func):
        return func
    
    class ChatClientAgent:
        def __init__(self, **kwargs):
            self.tools = kwargs.get('tools', [])
        async def run(self, message: str):
            return f"[Mock Response with tools: {len(self.tools)}] Processed: {message}"
    
    class AzureChatClient:
        pass
    
    class HostedCodeInterpreterTool:
        pass

from app.core.config import get_settings
from app.core.models import CodeExample, LearningLevel

logger = structlog.get_logger(__name__)

router = APIRouter()

# Request/Response Models
class NativeToolsRequest(BaseModel):
    """Request model for native Python function tools."""
    message: str = Field(..., description="User message requesting calculations or analysis", 
                        example="Calculate the venue budget for a $10,000 corporate event")
    tools: List[str] = Field(default=["budget_calculator", "venue_estimator"], 
                           description="List of tool names to enable")
    agent_type: str = Field(default="budget_analyst", description="Agent type to use")

class McpToolsRequest(BaseModel):
    """Request model for MCP (Model Context Protocol) tools."""
    message: str = Field(..., description="User message for external tool integration",
                        example="Search for wedding venues in San Francisco with capacity for 150 guests")
    mcp_tools: List[str] = Field(default=["venue_search", "weather_api"], 
                               description="MCP tools to enable")
    location: Optional[str] = Field(default=None, description="Location for searches")
    budget_range: Optional[str] = Field(default=None, description="Budget range")

class HostedToolsRequest(BaseModel):
    """Request model for hosted Code Interpreter tools."""
    message: str = Field(..., description="User message requiring data analysis or computation",
                        example="Create a budget breakdown chart for my event planning data")
    enable_code_interpreter: bool = Field(default=True)
    enable_file_analysis: bool = Field(default=False)
    data_context: Optional[Dict[str, Any]] = Field(default=None, description="Data for analysis")

class ToolsResponse(BaseModel):
    """Response model for tool-enhanced agent interactions."""
    agent_response: str
    tools_used: List[str]
    tool_results: Dict[str, Any]
    processing_time_ms: float
    explanation: Dict[str, Any]
    learning_notes: List[str]
    code_example: CodeExample

# Native Tool Functions
@ai_function
def calculate_venue_budget(
    total_budget: Annotated[float, Field(description="Total event budget in dollars")],
    venue_percentage: Annotated[float, Field(default=30.0, description="Percentage of budget for venue")] = 30.0
) -> Dict[str, Any]:
    """
    Calculate venue budget allocation for an event.
    
    Typically venues consume 25-40% of total event budget depending on event type.
    """
    venue_budget = total_budget * (venue_percentage / 100)
    remaining_budget = total_budget - venue_budget
    
    return {
        "venue_budget": venue_budget,
        "remaining_budget": remaining_budget,
        "percentage_allocated": venue_percentage,
        "budget_breakdown": {
            "venue": venue_budget,
            "catering_estimated": remaining_budget * 0.4,
            "entertainment_estimated": remaining_budget * 0.2,
            "decorations_estimated": remaining_budget * 0.15,
            "miscellaneous": remaining_budget * 0.25
        },
        "recommendations": [
            f"Venue budget of ${venue_budget:,.2f} is appropriate for this event size",
            "Consider negotiating package deals that include catering",
            "Reserve 10-15% of total budget for unexpected expenses"
        ]
    }

@ai_function
def estimate_catering_cost(
    attendee_count: Annotated[int, Field(description="Number of event attendees")],
    meal_type: Annotated[str, Field(description="Type of meal: breakfast, lunch, dinner, cocktails")] = "dinner",
    service_style: Annotated[str, Field(description="Service style: buffet, plated, cocktail, family")] = "plated"
) -> Dict[str, Any]:
    """
    Estimate catering costs based on attendee count and meal type.
    """
    # Base costs per person by meal type and service style
    cost_matrix = {
        "breakfast": {"buffet": 15, "plated": 25, "continental": 12},
        "lunch": {"buffet": 25, "plated": 35, "sandwich": 18, "salad": 22},
        "dinner": {"buffet": 45, "plated": 65, "family": 38},
        "cocktails": {"passed": 35, "stationed": 28, "bar_only": 20}
    }
    
    base_cost = cost_matrix.get(meal_type, {}).get(service_style, 40)
    total_food_cost = base_cost * attendee_count
    
    # Additional costs
    service_fee = total_food_cost * 0.18  # 18% service fee
    gratuity = total_food_cost * 0.20    # 20% gratuity
    tax = total_food_cost * 0.08         # 8% tax
    
    total_cost = total_food_cost + service_fee + gratuity + tax
    
    return {
        "attendee_count": attendee_count,
        "meal_type": meal_type,
        "service_style": service_style,
        "cost_per_person": base_cost,
        "food_cost": total_food_cost,
        "service_fee": service_fee,
        "gratuity": gratuity,
        "tax": tax,
        "total_cost": total_cost,
        "cost_per_person_total": total_cost / attendee_count,
        "recommendations": [
            f"Budget ${total_cost:,.2f} for {attendee_count} guests",
            f"Cost per person including all fees: ${total_cost/attendee_count:.2f}",
            "Consider seasonal menu adjustments for cost savings",
            "Ask about package deals that include service fees"
        ]
    }

@ai_function  
def calculate_event_timeline(
    event_date: Annotated[str, Field(description="Event date in YYYY-MM-DD format")],
    event_type: Annotated[str, Field(description="Type of event")] = "corporate_meeting",
    complexity: Annotated[str, Field(description="Event complexity: simple, moderate, complex")] = "moderate"
) -> Dict[str, Any]:
    """
    Generate event planning timeline with key milestones.
    """
    complexity_weeks = {
        "simple": 4,      # 4 weeks planning
        "moderate": 8,    # 8 weeks planning  
        "complex": 16     # 16 weeks planning
    }
    
    planning_weeks = complexity_weeks.get(complexity, 8)
    
    # Create timeline milestones
    milestones = []
    week_percentages = [0.9, 0.75, 0.5, 0.25, 0.1]  # Weeks before event
    
    milestone_tasks = [
        "Begin venue research and initial planning",
        "Secure venue and major vendors",
        "Finalize catering and entertainment", 
        "Send invitations and confirm logistics",
        "Final confirmations and setup planning"
    ]
    
    for i, (percentage, task) in enumerate(zip(week_percentages, milestone_tasks)):
        weeks_before = int(planning_weeks * percentage)
        milestones.append({
            f"milestone_{i+1}": {
                "weeks_before_event": weeks_before,
                "task": task,
                "priority": "high" if i >= 3 else "medium"
            }
        })
    
    return {
        "event_date": event_date,
        "event_type": event_type,
        "complexity": complexity,
        "total_planning_weeks": planning_weeks,
        "milestones": milestones,
        "critical_path": [
            "Venue selection (highest priority)",
            "Vendor booking (must follow venue)",
            "Guest communications (timing dependent)",
            "Final logistics (week of event)"
        ],
        "recommendations": [
            f"Start planning {planning_weeks} weeks before the event",
            "Book venue and major vendors as early as possible",
            "Maintain weekly check-ins on progress",
            "Have backup plans for critical vendors"
        ]
    }

# MCP Tool Simulation Functions
def simulate_venue_search(location: str, capacity: int, budget_range: str) -> Dict[str, Any]:
    """Simulate MCP venue search tool results."""
    venues = [
        {
            "name": f"Grand {location} Hotel",
            "capacity": capacity + 50,
            "price_range": "$150-200 per person",
            "amenities": ["Full catering", "A/V equipment", "Parking"],
            "rating": 4.5
        },
        {
            "name": f"{location} Convention Center",
            "capacity": capacity + 200,
            "price_range": "$75-120 per person", 
            "amenities": ["Flexible spaces", "Catering partnerships", "Large parking"],
            "rating": 4.2
        },
        {
            "name": f"Boutique {location} Event Space",
            "capacity": capacity - 20,
            "price_range": "$100-150 per person",
            "amenities": ["Historic charm", "Full bar", "Outdoor space"],
            "rating": 4.8
        }
    ]
    
    return {
        "search_location": location,
        "requested_capacity": capacity,
        "budget_range": budget_range,
        "venues_found": len(venues),
        "venues": venues,
        "search_metadata": {
            "search_time_ms": 234,
            "total_available": len(venues),
            "filters_applied": ["capacity", "location", "budget"]
        }
    }

def simulate_weather_forecast(location: str, event_date: str) -> Dict[str, Any]:
    """Simulate weather API for outdoor event planning."""
    import random
    
    # Simulate weather data
    conditions = ["sunny", "partly_cloudy", "cloudy", "light_rain", "rain"]
    condition = random.choice(conditions[:3])  # Bias toward good weather
    
    return {
        "location": location,
        "event_date": event_date,
        "forecast": {
            "condition": condition,
            "temperature_high": random.randint(68, 85),
            "temperature_low": random.randint(55, 70),
            "precipitation_chance": random.randint(0, 30),
            "wind_speed": random.randint(5, 15)
        },
        "recommendations": [
            "Consider backup indoor space if precipitation > 20%",
            "Provide heating if temperature below 60°F",
            "Plan for wind if speeds exceed 10 mph"
        ]
    }

# Learning Support Functions
def generate_tools_explanation(interaction_type: str) -> Dict[str, Any]:
    """Generate educational explanation for tool interactions."""
    explanations = {
        "native_tools": {
            "concept": "Native Python Function Tools",
            "what_happened": [
                "Defined Python functions decorated with @ai_function",
                "Agent automatically selected and called appropriate functions",
                "Function results were integrated into agent response",
                "Tool parameters were extracted from natural language"
            ],
            "key_learnings": [
                "Tools extend agent capabilities beyond conversation",
                "@ai_function decorator makes Python functions available to agents",
                "Type hints and Field descriptions help agents understand tool parameters",
                "Agents can combine multiple tools to solve complex problems"
            ],
            "microsoft_agent_framework_concepts": [
                "@ai_function: Decorator that exposes Python functions to agents",
                "Automatic parameter extraction from natural language",
                "Type safety with Pydantic Field annotations",
                "Tool result integration in conversational context"
            ]
        },
        "mcp_integration": {
            "concept": "MCP (Model Context Protocol) Integration", 
            "what_happened": [
                "Connected to external MCP server for specialized tools",
                "Agent accessed tools beyond local Python functions",
                "Integrated external data sources and APIs",
                "Combined local and remote tool capabilities"
            ],
            "key_learnings": [
                "MCP enables integration with external services and data",
                "Agents can access real-time information and external APIs",
                "MCP tools complement native Python function tools",
                "Proper error handling is crucial for external service integration"
            ],
            "microsoft_agent_framework_concepts": [
                "MCP protocol for external tool integration",
                "Service discovery and capability negotiation",
                "Error handling for external service failures",
                "Authentication and security for external services"
            ]
        },
        "hosted_tools": {
            "concept": "Hosted Code Interpreter",
            "what_happened": [
                "Agent used hosted computing environment for analysis",
                "Executed code safely in isolated sandbox environment",
                "Generated visualizations and performed data analysis",
                "Integrated computational results into conversation"
            ],
            "key_learnings": [
                "Hosted tools provide secure code execution environment",
                "Enable complex data analysis and visualization",
                "Useful for statistical analysis and chart generation",
                "Combine with file upload for data processing workflows"
            ],
            "microsoft_agent_framework_concepts": [
                "HostedCodeInterpreterTool for secure code execution",
                "Sandboxed environment for untrusted code",
                "Integration with data visualization libraries",
                "File handling and data analysis capabilities"
            ]
        }
    }
    return explanations.get(interaction_type, explanations["native_tools"])

def get_tools_learning_notes(level: str = "level_2") -> List[str]:
    """Get learning notes for Level 2."""
    return [
        "🔧 **Core Concept**: Tools extend agent capabilities beyond text generation",
        "⚡ **Best Practice**: Use type hints and clear descriptions for better tool parameter extraction",
        "🎯 **Tool Selection**: Agents automatically choose appropriate tools based on user requests",
        "🔄 **Integration**: Tools can be combined - agents may use multiple tools in a single response",
        "🛡️ **Security**: Hosted tools provide safe execution environments for untrusted code",
        "🌐 **Extensibility**: MCP protocol enables integration with virtually any external service",
        "📊 **Analytics**: Use hosted Code Interpreter for data analysis and visualization",
        "🎨 **Flexibility**: Mix native Python functions, MCP tools, and hosted capabilities"
    ]

def generate_tools_code_example(example_type: str, **kwargs) -> CodeExample:
    """Generate code examples for tool integration."""
    examples = {
        "native_tools": CodeExample(
            title="Agent with Native Python Tools",
            language="python",
            code="""
from agent_framework import ChatClientAgent, ai_function
from agent_framework.azure import AzureChatClient
from typing import Annotated
from pydantic import Field

# Define a tool function
@ai_function
def calculate_venue_budget(
    total_budget: Annotated[float, Field(description="Total event budget")],
    venue_percentage: Annotated[float, Field(default=30.0)] = 30.0
) -> dict:
    venue_budget = total_budget * (venue_percentage / 100)
    return {
        "venue_budget": venue_budget,
        "remaining_budget": total_budget - venue_budget,
        "recommendations": ["Consider negotiating package deals"]
    }

# Create agent with tools
agent = ChatClientAgent(
    name="BudgetAnalystAgent",
    tools=[calculate_venue_budget],  # Add tools here
    chat_client=AzureChatClient()
)

# Agent will automatically use tools when appropriate
response = await agent.run("Calculate venue budget for a $10,000 event")
""".strip(),
            explanation="Tools are Python functions decorated with @ai_function. Agents automatically select and call tools based on user requests. Type hints help extract parameters correctly.",
            level=LearningLevel.LEVEL_2
        ),
        "mcp_integration": CodeExample(
            title="Agent with MCP Tools",
            language="python",
            code="""
from agent_framework import ChatClientAgent
from agent_framework.mcp import McpClient

# Connect to MCP server
mcp_client = McpClient("venue-search-server")

# Create agent with MCP tools
agent = ChatClientAgent(
    name="VenueResearchAgent",
    mcp_client=mcp_client,
    tools=["venue_search", "weather_api"],  # MCP tool names
    chat_client=AzureChatClient()
)

# Agent can now access external venue databases
response = await agent.run(
    "Find wedding venues in San Francisco for 150 guests under $15k"
)
""".strip(),
            explanation="MCP (Model Context Protocol) enables agents to access external tools and data sources. Connect to MCP servers and specify available tools.",
            level=LearningLevel.LEVEL_2
        ),
        "hosted_tools": CodeExample(
            title="Agent with Hosted Code Interpreter",
            language="python", 
            code="""
from agent_framework import ChatClientAgent
from agent_framework.hosted import HostedCodeInterpreterTool

# Create agent with hosted code interpreter
agent = ChatClientAgent(
    name="DataAnalystAgent",
    tools=[HostedCodeInterpreterTool()],
    chat_client=AzureChatClient()
)

# Agent can now execute code and create visualizations
response = await agent.run(
    "Create a budget breakdown chart showing venue, catering, and entertainment costs"
)
""".strip(),
            explanation="HostedCodeInterpreterTool provides secure code execution for data analysis and visualization. Useful for statistical analysis and chart generation.",
            level=LearningLevel.LEVEL_2
        )
    }
    return examples.get(example_type, examples["native_tools"])

# API Endpoints
@router.get("/", summary="Agent Tools Overview")
async def agent_tools_overview():
    """Get comprehensive overview of agent tools capabilities and learning path."""
    return {
        "level": 2,
        "name": "Agent Tools",
        "description": "Learn to enhance agents with tools and capabilities",
        "learning_objectives": [
            "Understand how to create and use native Python function tools",
            "Learn MCP (Model Context Protocol) integration for external services",
            "Master hosted Code Interpreter for data analysis and visualization",
            "Combine multiple tool types in a single agent"
        ],
        "tool_types": {
            "native_tools": {
                "description": "Python functions decorated with @ai_function",
                "use_cases": ["Calculations", "Data processing", "Business logic"],
                "advantages": ["Fast execution", "Full control", "Type safety"]
            },
            "mcp_integration": {
                "description": "External tools via Model Context Protocol",
                "use_cases": ["Web APIs", "Database queries", "Third-party services"],
                "advantages": ["Real-time data", "External services", "Scalability"]
            },
            "hosted_tools": {
                "description": "Secure code execution environment",
                "use_cases": ["Data analysis", "Visualization", "Complex computations"],
                "advantages": ["Security", "No local setup", "Rich libraries"]
            }
        },
        "endpoints": [
            {
                "path": "/native_tools",
                "description": "Learn Python function tools with practical budget calculations",
                "example_request": "Calculate venue budget for $10,000 event"
            },
            {
                "path": "/mcp_integration", 
                "description": "Explore external tool integration via MCP protocol",
                "example_request": "Search for venues in San Francisco with capacity 150"
            },
            {
                "path": "/hosted_tools",
                "description": "Use hosted Code Interpreter for data analysis",
                "example_request": "Create budget breakdown visualization"
            }
        ]
    }

@router.post("/native_tools", response_model=ToolsResponse, summary="Native Python Function Tools")
async def native_tools_demo(
    request: NativeToolsRequest,
    settings = Depends(get_settings)
) -> ToolsResponse:
    """
    **Level 2 Learning Objective: Native Python Function Tools**
    
    Learn to create and use Python function tools with agents. This endpoint
    demonstrates how to define functions with @ai_function decorator and
    have agents automatically select and use them based on user requests.
    
    **What You'll Learn:**
    - How to create tool functions with @ai_function decorator
    - Type annotation best practices for tool parameters
    - How agents automatically select appropriate tools
    - Tool result integration in conversational responses
    
    **Available Native Tools:**
    - budget_calculator: Calculate venue and overall budget allocation
    - venue_estimator: Estimate venue costs based on requirements  
    - catering_calculator: Calculate catering costs per person
    - timeline_planner: Generate event planning timeline
    
    **Try These Examples:**
    - "Calculate venue budget for a $10,000 corporate event"
    - "Estimate catering costs for 75 people with plated dinner service"
    - "Create a planning timeline for a complex wedding in 6 months"
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("Processing native tools request", tools=request.tools)
        
        # Available native tools
        available_tools = {
            "budget_calculator": calculate_venue_budget,
            "venue_estimator": calculate_venue_budget,  # Alias
            "catering_calculator": estimate_catering_cost,
            "timeline_planner": calculate_event_timeline
        }
        
        # Select requested tools
        tools_to_use = [available_tools[tool] for tool in request.tools if tool in available_tools]
        
        # Create agent with tools
        agent = ChatClientAgent(
            name=f"{request.agent_type.replace('_', ' ').title()}Agent",
            description=f"Specialized {request.agent_type} with calculation tools",
            instructions=f"""
            You are a {request.agent_type} specialist with access to powerful calculation tools.
            
            When users ask for calculations, estimates, or analysis:
            - Automatically use the appropriate tools based on their request
            - Explain your calculations and reasoning
            - Provide actionable recommendations
            - Show both the raw numbers and their practical implications
            
            Available tools: {', '.join(request.tools)}
            """,
            tools=tools_to_use,
            chat_client=AzureChatClient()
        )
        
        # Process the message
        response = await agent.run(request.message)
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Simulate tool results for educational purposes
        tool_results = {
            "tools_called": request.tools,
            "example_calculation": "Budget calculation: $10,000 * 30% = $3,000 for venue"
        }
        
        return ToolsResponse(
            agent_response=response,
            tools_used=request.tools,
            tool_results=tool_results,
            processing_time_ms=processing_time,
            explanation=generate_tools_explanation("native_tools"),
            learning_notes=get_tools_learning_notes(),
            code_example=generate_tools_code_example("native_tools", tools=request.tools)
        )
        
    except Exception as e:
        logger.error("Error in native tools demo", error=str(e))
        raise HTTPException(status_code=500, detail=f"Tool processing failed: {str(e)}")

@router.post("/mcp_integration", response_model=ToolsResponse, summary="MCP Tool Integration")
async def mcp_integration_demo(
    request: McpToolsRequest,
    settings = Depends(get_settings)
) -> ToolsResponse:
    """
    **Level 2 Learning Objective: MCP (Model Context Protocol) Integration**
    
    Learn to integrate external tools and services using the Model Context Protocol.
    This enables agents to access real-time data, external APIs, and third-party services.
    
    **What You'll Learn:**
    - How to connect agents to MCP servers
    - Integration with external data sources and APIs
    - Combining local and remote tool capabilities
    - Error handling for external service calls
    
    **Available MCP Tools:**
    - venue_search: Search external venue databases
    - weather_api: Get weather forecasts for outdoor events
    - pricing_api: Get real-time pricing data
    - availability_checker: Check vendor availability
    
    **Try These Examples:**
    - "Find wedding venues in San Francisco for 150 guests under $15k"
    - "Check weather forecast for outdoor event next month in Chicago"
    - "Search for catering vendors available on June 15th"
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("Processing MCP tools request", mcp_tools=request.mcp_tools)
        
        # Simulate MCP tool results
        tool_results = {}
        
        if "venue_search" in request.mcp_tools and request.location:
            tool_results["venue_search"] = simulate_venue_search(
                location=request.location or "San Francisco",
                capacity=150,  # Default capacity
                budget_range=request.budget_range or "$10k-15k"
            )
        
        if "weather_api" in request.mcp_tools:
            tool_results["weather_api"] = simulate_weather_forecast(
                location=request.location or "San Francisco",
                event_date="2024-06-15"  # Example date
            )
        
        # Create agent with MCP capabilities
        agent = ChatClientAgent(
            name="VenueResearchAgent",
            description="Specialized agent with external data access via MCP",
            instructions="""
            You are a venue research specialist with access to external data sources.
            
            You can:
            - Search comprehensive venue databases
            - Get real-time weather forecasts
            - Check current pricing and availability
            - Access third-party service APIs
            
            Always provide:
            - Multiple options with comparisons
            - Current and accurate information
            - Practical recommendations based on real data
            """,
            # Note: In real implementation, would connect to actual MCP server
            chat_client=AzureChatClient()
        )
        
        # Enhance response with tool results
        base_response = await agent.run(request.message)
        enhanced_response = f"{base_response}\n\nBased on external data sources:\n"
        
        if "venue_search" in tool_results:
            venues = tool_results["venue_search"]["venues"]
            enhanced_response += f"Found {len(venues)} venues matching your criteria:\n"
            for venue in venues:
                enhanced_response += f"- {venue['name']}: {venue['capacity']} capacity, {venue['price_range']}\n"
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ToolsResponse(
            agent_response=enhanced_response,
            tools_used=request.mcp_tools,
            tool_results=tool_results,
            processing_time_ms=processing_time,
            explanation=generate_tools_explanation("mcp_integration"),
            learning_notes=get_tools_learning_notes(),
            code_example=generate_tools_code_example("mcp_integration", mcp_tools=request.mcp_tools)
        )
        
    except Exception as e:
        logger.error("Error in MCP tools demo", error=str(e))
        raise HTTPException(status_code=500, detail=f"MCP tool processing failed: {str(e)}")

@router.post("/hosted_tools", response_model=ToolsResponse, summary="Hosted Code Interpreter Tools") 
async def hosted_tools_demo(
    request: HostedToolsRequest,
    settings = Depends(get_settings)
) -> ToolsResponse:
    """
    **Level 2 Learning Objective: Hosted Code Interpreter**
    
    Learn to use hosted computing environments for secure code execution,
    data analysis, and visualization. Perfect for statistical analysis,
    chart generation, and complex computations.
    
    **What You'll Learn:**
    - How to enable hosted code execution in agents
    - Secure sandboxed environment for untrusted code
    - Data analysis and visualization capabilities  
    - Integration with popular Python libraries (pandas, matplotlib, etc.)
    
    **Hosted Tool Capabilities:**
    - Python code execution in secure sandbox
    - Data analysis with pandas and numpy
    - Visualization with matplotlib and seaborn
    - File upload and processing
    - Statistical analysis and modeling
    
    **Try These Examples:**
    - "Create a budget breakdown pie chart for my $10k event"
    - "Analyze guest RSVP trends over the past month"
    - "Generate a timeline visualization for event planning milestones"
    - "Calculate statistical significance of catering preference survey"
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("Processing hosted tools request", 
                   code_interpreter=request.enable_code_interpreter)
        
        # Create agent with hosted code interpreter
        tools = []
        if request.enable_code_interpreter:
            tools.append(HostedCodeInterpreterTool())
        
        agent = ChatClientAgent(
            name="DataAnalystAgent", 
            description="Specialist in data analysis and visualization using hosted tools",
            instructions="""
            You are a data analysis specialist with access to a secure code execution environment.
            
            You can:
            - Execute Python code safely in a sandboxed environment
            - Create visualizations and charts
            - Perform statistical analysis
            - Process and analyze data files
            
            When users request analysis or visualizations:
            - Write clear, well-commented code
            - Use appropriate libraries (pandas, matplotlib, seaborn, numpy)
            - Explain your methodology and results
            - Provide actionable insights from the data
            """,
            tools=tools,
            chat_client=AzureChatClient()
        )
        
        # Process the message
        response = await agent.run(request.message)
        
        # Simulate code execution results for educational purposes
        simulated_code_result = {
            "code_executed": "import matplotlib.pyplot as plt; plt.pie([3000, 2500, 2000], labels=['Venue', 'Catering', 'Entertainment'])",
            "visualization_created": "budget_breakdown_chart.png",
            "data_analysis": {
                "venue_percentage": 42.8,
                "catering_percentage": 35.7,
                "entertainment_percentage": 28.5
            }
        }
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ToolsResponse(
            agent_response=response,
            tools_used=["hosted_code_interpreter"] if request.enable_code_interpreter else [],
            tool_results={
                "hosted_execution": simulated_code_result,
                "sandbox_info": {
                    "environment": "Python 3.11 with data science libraries",
                    "available_libraries": ["pandas", "numpy", "matplotlib", "seaborn", "scipy"],
                    "execution_timeout": "30 seconds",
                    "memory_limit": "1GB"
                }
            },
            processing_time_ms=processing_time,
            explanation=generate_tools_explanation("hosted_tools"),
            learning_notes=get_tools_learning_notes(),
            code_example=generate_tools_code_example("hosted_tools")
        )
        
    except Exception as e:
        logger.error("Error in hosted tools demo", error=str(e))
        raise HTTPException(status_code=500, detail=f"Hosted tool processing failed: {str(e)}")

@router.get("/examples", summary="Agent Tools Code Examples")
async def get_agent_tools_examples():
    """
    Get comprehensive code examples for all types of agent tools.
    
    This endpoint provides ready-to-use examples demonstrating native tools,
    MCP integration, and hosted code interpreter usage patterns.
    """
    return {
        "native_tools_examples": [
            {
                "title": "Budget Calculator Tool",
                "description": "Create a tool for event budget calculations",
                "code": """
@ai_function
def calculate_venue_budget(
    total_budget: Annotated[float, Field(description="Total event budget")],
    venue_percentage: Annotated[float, Field(default=30.0)] = 30.0
) -> dict:
    venue_budget = total_budget * (venue_percentage / 100)
    return {
        "venue_budget": venue_budget,
        "remaining_budget": total_budget - venue_budget
    }

agent = ChatClientAgent(
    name="BudgetAnalyst",
    tools=[calculate_venue_budget],
    chat_client=AzureChatClient()
)
                """,
                "use_cases": ["Budget planning", "Cost estimation", "Financial analysis"]
            }
        ],
        "mcp_examples": [
            {
                "title": "Venue Search Integration",
                "description": "Connect to external venue databases via MCP",
                "code": """
from agent_framework.mcp import McpClient

mcp_client = McpClient("venue-search-server")
agent = ChatClientAgent(
    name="VenueResearcher",
    mcp_client=mcp_client,
    tools=["venue_search", "availability_check"],
    chat_client=AzureChatClient()
)
                """,
                "use_cases": ["Real-time data access", "External APIs", "Third-party services"]
            }
        ],
        "hosted_tools_examples": [
            {
                "title": "Data Analysis with Code Interpreter", 
                "description": "Use hosted environment for secure code execution",
                "code": """
from agent_framework.hosted import HostedCodeInterpreterTool

agent = ChatClientAgent(
    name="DataAnalyst",
    tools=[HostedCodeInterpreterTool()],
    chat_client=AzureChatClient()
)

# Agent can now execute code and create visualizations
response = await agent.run("Create a budget breakdown chart")
                """,
                "use_cases": ["Data visualization", "Statistical analysis", "File processing"]
            }
        ],
        "best_practices": [
            "Use clear, descriptive function names and documentation",
            "Implement proper error handling for all tools",
            "Validate input parameters with type hints and Field constraints",
            "Return structured data that agents can easily interpret",
            "Test tools independently before integrating with agents",
            "Consider security implications, especially for hosted tools",
            "Monitor tool performance and usage patterns",
            "Provide meaningful error messages for debugging"
        ]
    }