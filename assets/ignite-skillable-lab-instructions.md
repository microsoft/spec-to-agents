# Build A2A and MCP Systems using SWE Agents and agent-framework

## Lab Scenario

In this lab, you'll build a sophisticated multi-agent event planning system using **[Microsoft Agent Framework](https://github.com/microsoft/agent-framework)**, an enterprise-ready framework that combines the best of Semantic Kernel and AutoGen. You'll create specialized AI agents that collaborate to plan comprehensive events, learning how to:

- **Build Multi-Agent Workflows**: Orchestrate multiple specialized agents (Event Coordinator, Venue Specialist, Budget Analyst, Catering Coordinator, and Logistics Manager) working together
- **Implement A2A (Agent-to-Agent) Protocol**: Enable direct agent-to-agent communication for collaborative problem-solving
- **Integrate MCP (Model Context Protocol) Tools**: Connect external capabilities like weather forecasting, calendar management, and sequential reasoning
- **Deploy to Azure AI Foundry**: Run your agents in Azure AI Agents Service with full observability
- **Visualize with DevUI**: See real-time agent interactions and workflow execution

The system demonstrates concurrent workflow execution patterns where agents work in parallel, exchange information, and synthesize comprehensive event plans. You'll implement human-in-the-loop capabilities, allowing user input at critical decision points during agent execution.

![Event Planning Workflow Architecture](https://raw.githubusercontent.com/microsoft/spec-to-agents/main/assets/workflow_architecture.png)

---

## Understanding Key Protocols: A2A and MCP

Before diving into the lab, let's understand two fundamental protocols that power modern AI agent systems:

### **Agent-to-Agent (A2A) Protocol**

A2A is an emerging standard for enabling direct communication between AI agents. In traditional systems, agents communicate through a central orchestrator. With A2A:

- **Direct Communication**: Agents can message each other directly, reducing latency and enabling more natural collaboration
- **Standardized Messaging**: A common protocol ensures agents built with different frameworks can still communicate
- **Workflow Flexibility**: Agents can dynamically determine which other agents to involve based on the task

**In this lab**, your agents use A2A patterns to pass context between specialists (e.g., Budget Analyst receives venue recommendations from Venue Specialist).

### **Model Context Protocol (MCP)**

MCP is an open standard that defines how AI models access external tools and data sources. Think of it as a universal adapter:

- **Tool Discovery**: AI models can discover what tools are available and how to use them
- **Standardized Invocation**: Tools are called using a consistent interface, regardless of implementation
- **Bidirectional Integration**: Tools can be called by agents, and tools can invoke agents

**In this lab**, your agents use MCP tools like:
- **sequential-thinking-tools**: Advanced reasoning for complex planning tasks
- **Weather forecasting**: External API integration via MCP
- **Calendar management**: Persistent scheduling capabilities

MCP enables your locally-defined Python functions to become discoverable, callable tools for any MCP-compatible AI system.

---

## 1  Lab Set-Up Snapshot

Your lab environment comes pre-configured with:

- **Visual Studio Code** - Primary development environment
- **Edge - GitHub & Azure Portals** - Pre-configured browser tabs
- **Python 3.13** - Latest stable version
- **uv** - Fast Python package manager
- **Azure CLI** - Manage Azure resources
- **Azure Developer CLI (azd)** - Simplified deployment workflows
- **Node.js 18+** - Required for MCP tools
- **Git** - Source control

> [!hint] **Ignore Sign-In Notifications**
> 
> You may see blue "Sign in required" notifications or "Activate Windows" watermarks. Simply click "Not now" and continue - these won't affect your lab experience.

From your Desktop (or Taskbar), open the **Edge - GitHub & Azure Portals** shortcut with three tabs:
1. **spec-to-agents GitHub Repo**: *https://github.com/microsoft/spec-to-agents*
2. **Azure Portal**: *https://portal.azure.com*
3. **Azure AI Foundry**: *https://ai.azure.com*

---

## 2  Fork the Repository

1. In Edge, navigate to the **spec-to-agents** GitHub tab and click **Fork → Create fork**.

> [!hint] **Enter your GitHub username** below to auto-populate commands:
> @lab.TextBox(github-username)

2. After forking completes, validate your fork's HTTPS URL:
   
   **++https://github.com/@lab.Variable(github-username)/spec-to-agents.git++**

---

## 3  Clone and Set Up the Repository

1. Launch **Visual Studio Code** from the Taskbar.

2. Open a new **Terminal** (*Terminal → New Terminal*).

3. Clone your fork and open the project (click the **T** icon next to the script below to copy, **validate @lab.Variable(github-username)** is correct):

   ```powershell
   # Clone your fork
   git clone https://github.com/@lab.Variable(github-username)/spec-to-agents.git
   cd spec-to-agents

   # Open in VS Code
   code . --reuse-window
   ```

4. VS Code will reload with the **spec-to-agents** folder open.

---

## 4  Start Azure Resource Provisioning (Background Process)

You'll use Azure Developer CLI (azd) to provision all necessary Azure resources. This process takes 5-10 minutes and runs in the background while you work on coding exercises.

1. **Login to azd** (ensure you're in the *spec-to-agents* root directory):
   
   **+++azd auth login+++**

   - Username: **+++@lab.CloudPortalCredential(User1).Username+++**  
   - Password: **+++@lab.CloudPortalCredential(User1).Password+++**
   
   Authenticate in your browser, then close the tab and return to VS Code.

2. **Create azd Environment**:

   **+++azd env new agents-lab-@lab.LabInstance.Id --subscription @lab.CloudSubscription.Id --location @lab.CloudResourceGroup(ResourceGroup1).Location+++**

3. **Start Provisioning** (do not wait for completion):
   
   **+++azd provision+++**

> [!knowledge] **Resources Being Provisioned**
> 
> This creates:
> - Azure AI Foundry Hub and Project
> - Azure OpenAI Service (gpt-4o, text-embedding-3-small)
> - Azure Cosmos DB for NoSQL (agent state storage)
> - Azure Storage Account
> - Azure AI Search
> - Azure Application Insights
> - Azure Container Apps (for DevUI hosting)

**Proceed to coding exercises while provisioning runs in the background.**

---

## 5  Understanding Microsoft Agent Framework

Before implementing code, let's understand the Agent Framework architecture.

### Core Concepts

**1. Agents**
```python
from agent_framework import ChatAgent

# Create a specialized agent
agent = client.create_agent(
    name="VenueSpecialist",
    instructions="You are an expert in venue selection...",
    tools=[bing_search, mcp_tool],
    store=True
)
```

**2. Workflows**
```python
from agent_framework import Workflow, WorkflowBuilder

# Orchestrate multiple agents
workflow = (
    WorkflowBuilder(name="Event Planning")
    .set_start_executor(coordinator)
    .add_edge(coordinator, venue_specialist)
    .add_edge(venue_specialist, budget_analyst)
    .build()
)
```

**3. Executors**
```python
from agent_framework import AgentExecutor

# Wrap agents for workflow execution
venue_exec = AgentExecutor(agent=venue_agent, id="venue")
```

**4. Tools**
```python
from agent_framework import ai_function

@ai_function
async def get_weather_forecast(location: str, days: int = 3) -> str:
    """Get weather forecast for event planning."""
    # Implementation
```

### Key Features

- **Multi-Language Support**: Python and .NET implementations
- **Enterprise-Ready**: Built on Semantic Kernel's production-proven infrastructure
- **AutoGen Patterns**: Multi-agent conversation and orchestration patterns
- **Azure Integration**: Native support for Azure AI services
- **DevUI**: Real-time visualization of agent interactions

---

## 6  Coding Exercises: Build Your Multi-Agent System

Now you'll implement the core functionality of your event planning system. Open **src/spec_to_agents/workflow/core.py** in VS Code.

### Exercise 1: Configure Agent Tools

**Concept**: Each agent needs specific tools to perform its job. The Venue Specialist needs web search, the Budget Analyst needs code execution for calculations, and the Logistics Manager needs calendar and weather tools.

**Locate** the `# TODO: Lab Exercise 1` comment in **core.py** (around line 65).

**Replace** the existing tool configurations with:

```python
# TODO: Lab Exercise 1 - Configure specialized tools for each agent

# Get MCP sequential thinking tool for advanced reasoning
mcp_tool = await get_sequential_thinking_tool()

# Create hosted Azure AI tools
bing_search = HostedWebSearchTool(
    name="Bing Search",
    description="Search the web for current information with source citations"
)

code_interpreter = HostedCodeInterpreterTool(
    description=(
        "Execute Python code for financial calculations, budget analysis, "
        "and data visualization with automatic scratchpad creation"
    )
)

# Coordinator: MCP tool for orchestration reasoning
coordinator_agent = client.create_agent(
    name="EventCoordinator",
    instructions=event_coordinator.SYSTEM_PROMPT,
    tools=[mcp_tool],
    store=True,
)

# Venue Specialist: Web search + reasoning + user input
venue_agent = client.create_agent(
    name="VenueSpecialist",
    instructions=venue_specialist.SYSTEM_PROMPT,
    tools=[bing_search, mcp_tool, request_user_input],
    store=True,
)

# Budget Analyst: Code execution + reasoning + user input
budget_agent = client.create_agent(
    name="BudgetAnalyst",
    instructions=budget_analyst.SYSTEM_PROMPT,
    tools=[code_interpreter, mcp_tool, request_user_input],
    store=True,
)

# Catering: Web search + reasoning + user input
catering_agent = client.create_agent(
    name="CateringCoordinator",
    instructions=catering_coordinator.SYSTEM_PROMPT,
    tools=[bing_search, mcp_tool, request_user_input],
    store=True,
)

# Logistics: Calendar + weather + reasoning + user input
logistics_agent = client.create_agent(
    name="LogisticsManager",
    instructions=logistics_manager.SYSTEM_PROMPT,
    tools=[
        get_weather_forecast,
        create_calendar_event,
        list_calendar_events,
        delete_calendar_event,
        mcp_tool,
        request_user_input,
    ],
    store=True,
)
```

> [!knowledge] **Why These Tool Combinations?**
> 
> - **Venue Specialist**: Needs web search to find venues online and research options
> - **Budget Analyst**: Requires code execution for complex financial calculations
> - **Catering Coordinator**: Uses web search for menu research and caterer information
> - **Logistics Manager**: Needs calendar tools for scheduling and weather for outdoor planning
> - **All Specialists**: Include MCP sequential-thinking for breaking down complex decisions
> - **All Specialists**: Include request_user_input for human-in-the-loop approval

### Exercise 2: Build the Workflow with A2A Communication

**Concept**: The WorkflowBuilder defines how agents communicate. Each edge represents a potential A2A communication path. The workflow implements a sequential pattern where output from one agent becomes input to the next.

**Locate** the `# TODO: Lab Exercise 2` comment in **core.py** (around line 130).

**Replace** the workflow building code with:

```python
# TODO: Lab Exercise 2 - Build workflow with A2A communication edges

# Create AgentExecutors (wrappers for workflow integration)
coordinator_exec = AgentExecutor(agent=coordinator_agent, id="coordinator")
venue_exec = AgentExecutor(agent=venue_agent, id="venue")
budget_exec = AgentExecutor(agent=budget_agent, id="budget")
catering_exec = AgentExecutor(agent=catering_agent, id="catering")
logistics_exec = AgentExecutor(agent=logistics_agent, id="logistics")

# Create RequestInfoExecutor for human-in-the-loop
request_info = RequestInfoExecutor(id="user_input")

# Create HITL (Human-In-The-Loop) wrappers
venue_hitl = HumanInLoopAgentExecutor(agent_id="venue", request_info_id="user_input")
budget_hitl = HumanInLoopAgentExecutor(agent_id="budget", request_info_id="user_input")
catering_hitl = HumanInLoopAgentExecutor(agent_id="catering", request_info_id="user_input")
logistics_hitl = HumanInLoopAgentExecutor(agent_id="logistics", request_info_id="user_input")

# Build workflow with A2A edges
workflow = (
    WorkflowBuilder(
        name="Event Planning Workflow",
        description=(
            "Multi-agent event planning workflow with venue selection, budgeting, "
            "catering, and logistics coordination"
        ),
    )
    # Set entry point
    .set_start_executor(coordinator_exec)
    
    # A2A sequential flow: Coordinator → Venue → Budget → Catering → Logistics → Coordinator
    .add_edge(coordinator_exec, venue_exec)
    .add_edge(venue_exec, venue_hitl)
    .add_edge(venue_hitl, budget_exec)
    .add_edge(budget_exec, budget_hitl)
    .add_edge(budget_hitl, catering_exec)
    .add_edge(catering_exec, catering_hitl)
    .add_edge(catering_hitl, logistics_exec)
    .add_edge(logistics_exec, logistics_hitl)
    .add_edge(logistics_hitl, coordinator_exec)  # Back to coordinator for synthesis
    
    # Human-in-the-loop bidirectional edges
    .add_edge(venue_hitl, request_info)
    .add_edge(request_info, venue_hitl)
    .add_edge(budget_hitl, request_info)
    .add_edge(request_info, budget_hitl)
    .add_edge(catering_hitl, request_info)
    .add_edge(request_info, catering_hitl)
    .add_edge(logistics_hitl, request_info)
    .add_edge(request_info, logistics_hitl)
    
    .build()
)

# Set stable ID for DevUI
workflow.id = "event-planning-workflow"
```

> [!knowledge] **Understanding A2A Communication in This Workflow**
> 
> The workflow implements A2A patterns through edges:
> 
> 1. **Sequential Delegation**: Coordinator delegates to each specialist in sequence
> 2. **Context Passing**: Each agent receives the conversation history from previous agents
> 3. **HITL Integration**: Agents can pause for user input via bidirectional edges with RequestInfoExecutor
> 4. **Synthesis Loop**: Final edge loops back to Coordinator to synthesize all recommendations
> 
> This creates a dynamic conversation flow where agents build on each other's outputs.

### Exercise 3: Implement Custom MCP Tool

**Concept**: MCP tools can be defined as simple Python functions with the `@ai_function` decorator. Let's add a custom tool to enhance the Logistics Manager's capabilities.

**Open** **src/spec_to_agents/tools/weather.py** and locate `# TODO: Lab Exercise 3`.

**Add** this enhanced error handling:

```python
# TODO: Lab Exercise 3 - Add enhanced error handling for weather tool

@ai_function
async def get_weather_forecast(
    location: Annotated[
        str, Field(description="City name or 'latitude,longitude' (e.g., 'Seattle' or '47.6062,-122.3321')")
    ],
    days: Annotated[int, Field(description="Number of forecast days (1-7)", ge=1, le=7)] = 3,
) -> str:
    """Get weather forecast for event planning using Open-Meteo API."""
    async with httpx.AsyncClient() as client:
        try:
            # Geocoding logic
            if "," in location:
                try:
                    lat, lon = map(float, location.split(","))
                    location_name = f"{lat:.4f}°, {lon:.4f}°"
                except ValueError:
                    return "Error: Invalid coordinates format. Use 'latitude,longitude'"
            else:
                # Geocode city name
                geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
                geocode_params = {"name": location, "count": 1, "language": "en"}
                geocode_response = await client.get(geocode_url, params=geocode_params)
                geocode_response.raise_for_status()
                geocode_data = geocode_response.json()

                if not geocode_data.get("results"):
                    return f"Error: Location '{location}' not found"

                result = geocode_data["results"][0]
                lat = result["latitude"]
                lon = result["longitude"]
                location_name = f"{result['name']}, {result.get('country', 'Unknown')}"

            # Get forecast
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": days,
            }

            weather_response = await client.get(weather_url, params=weather_params)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            # Format results (weather codes mapping omitted for brevity)
            daily = weather_data["daily"]
            forecasts = []
            for i in range(len(daily["time"])):
                date = daily["time"][i]
                temp_max = daily["temperature_2m_max"][i]
                temp_min = daily["temperature_2m_min"][i]
                precip_prob = daily["precipitation_probability_max"][i]
                
                forecasts.append(
                    f"{date}: {temp_min:.1f}°C to {temp_max:.1f}°C, "
                    f"{precip_prob}% precipitation"
                )

            return f"Weather forecast for {location_name}:\n" + "\n".join(forecasts)

        except httpx.HTTPStatusError as e:
            return f"Error fetching weather: {e.response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
```

> [!knowledge] **MCP Tool Best Practices**
> 
> - Use type hints with `Annotated` and `Field` for parameter documentation
> - Provide clear descriptions that help LLMs understand when to use the tool
> - Return structured, parseable text responses
> - Handle errors gracefully with informative messages
> - Use async/await for I/O operations

### Exercise 4: Understand Human-in-the-Loop Integration

**Concept**: The `HumanInLoopAgentExecutor` intercepts tool calls to `request_user_input`, pausing workflow execution until the user responds via DevUI.

**Open** **src/spec_to_agents/workflow/executors.py** and **review** the implementation:

```python
class HumanInLoopAgentExecutor(Executor):
    """
    Wraps AgentExecutor to enable human-in-the-loop via request_user_input tool.
    
    Flow:
    1. Agent calls request_user_input tool
    2. This executor intercepts the FunctionCallContent
    3. Emits UserElicitationRequest to RequestInfoExecutor
    4. Workflow pauses until user responds in DevUI
    5. Receives RequestResponse and continues workflow
    """

    @handler
    async def from_response(
        self, response: AgentExecutorResponse, 
        ctx: WorkflowContext[UserElicitationRequest | AgentExecutorResponse]
    ) -> None:
        """Check for request_user_input tool calls."""
        self._current_response = response

        user_request = self._extract_user_request(response)

        if user_request:
            # Emit request to RequestInfoExecutor - workflow pauses
            await ctx.send_message(
                UserElicitationRequest(
                    prompt=user_request.get("prompt", ""),
                    context=user_request.get("context", {}),
                    request_type=user_request.get("request_type", "clarification"),
                ),
                target_id=self._request_info_id,
            )
        else:
            # No user input needed - continue to next agent
            await ctx.send_message(response)

    @handler
    async def accept_human_response(
        self, response: RequestResponse[UserElicitationRequest, str],
        ctx: WorkflowContext[AgentExecutorResponse]
    ) -> None:
        """User responded - continue workflow."""
        if self._current_response:
            await ctx.send_message(self._current_response)
```

> [!knowledge] **HITL Pattern Benefits**
> 
> - **Flexible Approval Gates**: Agents decide when user input is needed
> - **Context-Aware**: User sees agent's reasoning and proposed recommendations
> - **Non-Blocking**: Other agents can continue while waiting for input
> - **DevUI Integration**: Seamless UI for user interaction

---

## 7  Install Python Dependencies

1. Navigate to the **src** directory:
   ```powershell
   cd $HOME\spec-to-agents\src  # Or appropriate path
   ```

2. Create and activate virtual environment:
   ```powershell
   uv venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```powershell
   uv pip install -r requirements.txt
   ```

---

## 8  Verify Provisioning and Local Settings

1. Check the terminal where `azd provision` is running. Wait for successful completion.

2. After provisioning, verify **src/.env** was created with values like:
   ```
   AZURE_OPENAI_ENDPOINT=https://...
   PROJECT_CONNECTION_STRING=...
   AGENTS_MODEL_DEPLOYMENT_NAME=gpt-4o
   EMBEDDING_MODEL_DEPLOYMENT_NAME=text-embedding-3-small
   ```

3. If `.env` is missing, manually run:
   ```powershell
   # From spec-to-agents root
   .\scripts\generate-settings.ps1
   ```

---

## 9  Run Locally with DevUI

Now test your multi-agent system locally:

1. Start the application (from **src** directory with venv activated):
   ```powershell
   uv run app
   ```

2. DevUI opens automatically at **http://localhost:8080**. You'll see:
   - **Event Planning Workflow** in the workflows list
   - Visual representation of the workflow graph
   - Interactive chat interface

3. **Test the Workflow**:
   - Click on **Event Planning Workflow**
   - Click **Start New Session**
   - Enter a prompt: **Plan a tech conference for 100 people in Seattle with a $10,000 budget**
   - Watch agents execute in sequence:
     - Event Coordinator analyzes requirements
     - Venue Specialist searches for venues
     - Budget Analyst creates allocation
     - Catering Coordinator plans menu
     - Logistics Manager creates timeline
     - Event Coordinator synthesizes final plan

4. **Human-in-the-Loop Testing**:
   - Some agents may pause and request input
   - You'll see prompts like "Which venue do you prefer?"
   - Provide responses and watch the workflow continue

5. **Explore DevUI Features**:
   - **Messages Tab**: See conversation history between agents
   - **Workflow Graph**: Visual representation of agent interactions
   - **Logs**: Detailed execution logs including tool calls

![DevUI Event Planning](https://raw.githubusercontent.com/microsoft/spec-to-agents/main/assets/agent_tools.png)

> [!knowledge] **Understanding the DevUI Interface**
> 
> DevUI provides real-time observability:
> - **Node Colors**: Indicate agent execution status (running, completed, waiting)
> - **Edge Animations**: Show message passing between agents
> - **Tool Call Indicators**: Display when agents invoke tools
> - **Human Input Prompts**: Clearly marked pause points

---

## 10  Deploy to Azure

Deploy your multi-agent system to Azure:

1. Stop the local DevUI (Ctrl+C)

2. Deploy application code:
   ```powershell
   cd $HOME\spec-to-agents  # Root directory
   azd deploy
   ```

3. AZD will:
   - Package your application
   - Deploy to Azure Container Apps
   - Configure environment variables
   - Output the deployed endpoint URL

4. Note the **DevUI URL** from the output (e.g., `https://devui-...azurecontainerapps.io`)

---

## 11  Explore Azure AI Foundry Integration

Your agents are now running in Azure AI Agents Service. Let's explore:

1. Open **Azure AI Foundry** (https://ai.azure.com) in Edge

2. Navigate to your project: **agents-lab-@lab.LabInstance.Id**

3. **View Deployed Agents**:
   - Click **Agents** in the left navigation
   - See all five specialist agents listed
   - Click any agent to view configuration

4. **Explore Agent Runs**:
   - Click **Runs** to see execution history
   - Select a run to view detailed traces
   - Examine tool calls, message exchanges, and reasoning

5. **Test Agents Directly**:
   - Click **Playground**
   - Select **Event Planning Workflow**
   - Try prompts like:
     - "Plan a wedding for 150 guests in San Francisco"
     - "Organize a product launch event with $50k budget"

6. **Monitor with Application Insights**:
   - Azure Portal → Your Resource Group
   - Click **Application Insights** resource
   - View **Live Metrics** during execution
   - Explore **Application Map** to see service dependencies

---

## 12  Understanding A2A and MCP Integration

Let's review what you've built:

### **A2A Communication Flow**

```
User Input
    ↓
Event Coordinator (Analyzes requirements)
    ↓ [A2A: Delegates with context]
Venue Specialist (Searches venues)
    ↓ [A2A: Passes venue recommendations]
Budget Analyst (Allocates budget)
    ↓ [A2A: Passes budget breakdown]
Catering Coordinator (Plans menu)
    ↓ [A2A: Passes catering plan]
Logistics Manager (Creates timeline)
    ↓ [A2A: Returns to coordinator]
Event Coordinator (Synthesizes final plan)
    ↓
Complete Event Plan
```

### **MCP Tools in Action**

Your agents used these MCP tools:

1. **sequential-thinking-tools** (MCP Server)
   - Complex reasoning and planning
   - Breaking down tasks into steps
   - Used by: All agents

2. **Bing Search** (Hosted Tool)
   - Web search for venues and caterers
   - Used by: Venue Specialist, Catering Coordinator

3. **Code Interpreter** (Hosted Tool)
   - Financial calculations
   - Used by: Budget Analyst

4. **Weather Forecast** (Custom MCP Tool)
   - Event date weather checking
   - Used by: Logistics Manager

5. **Calendar Tools** (Custom MCP Tools)
   - Event scheduling
   - Used by: Logistics Manager

---

## 13  Advanced: Multi-Agent Patterns

Your system demonstrates several key patterns:

### **1. Sequential Workflow**
```python
.add_edge(coordinator, venue)
.add_edge(venue, budget)
.add_edge(budget, catering)
```
Each agent builds on previous outputs.

### **2. Human-in-the-Loop**
```python
.add_edge(venue_agent, venue_hitl)
.add_edge(venue_hitl, request_info)
.add_edge(request_info, venue_hitl)
```
Bidirectional edges enable pause/resume.

### **3. Tool Orchestration**
```python
tools=[bing_search, mcp_tool, request_user_input]
```
Each agent has specialized capabilities.

### **4. Synthesis Pattern**
```python
.add_edge(logistics_hitl, coordinator)
```
Final agent aggregates all recommendations.

---

## 14  Bonus Exercises (Optional)

### **Bonus 1: Add a New Agent**

Add a "Marketing Specialist" agent:

1. Create **src/spec_to_agents/prompts/marketing_specialist.py**
2. Create **src/spec_to_agents/agents/marketing_specialist.py**
3. Update **workflow/core.py** to include the agent
4. Add edges in the workflow

### **Bonus 2: Custom MCP Tool**

Create a "venue_availability_checker" tool:

1. Add to **src/spec_to_agents/tools/**
2. Integrate with Venue Specialist
3. Test in DevUI

### **Bonus 3: Parallel Execution**

Modify workflow for parallel venue and catering research:

```python
# Fork after coordinator
.add_edge(coordinator, venue)
.add_edge(coordinator, catering)

# Join before budget
.add_edge(venue, join_executor)
.add_edge(catering, join_executor)
.add_edge(join_executor, budget)
```

---

## 15  Clean-Up

> [!alert] **Important: Lab Environment Auto-Cleanup**
> 
> This lab environment will be automatically deleted after completion. Follow these steps to properly clean up Azure resources and sign out of accounts.

1. **Delete Azure Resources**:
   ```powershell
   cd $HOME\spec-to-agents
   azd down --purge --force
   ```

2. **Sign Out**:
   - VS Code: Profile icon → Sign Out
   - Edge: Sign out from GitHub, Azure Portal, Azure AI Foundry

---

## Conclusion

Congratulations! You've successfully built a production-ready multi-agent system using Microsoft Agent Framework. You've learned:

### **Core Achievements**

✅ **Multi-Agent Orchestration**: Built five specialized agents working collaboratively  
✅ **A2A Protocol**: Implemented agent-to-agent communication patterns  
✅ **MCP Integration**: Connected external tools via Model Context Protocol  
✅ **Azure AI Foundry**: Deployed to Azure AI Agents Service  
✅ **DevUI**: Visualized real-time agent interactions  
✅ **Human-in-the-Loop**: Implemented approval gates and user interaction  

### **Key Technologies Mastered**

- **Microsoft Agent Framework**: Enterprise-grade multi-agent orchestration
- **Azure AI Agents Service**: Managed AI agent execution
- **MCP Tools**: Standardized tool integration
- **A2A Communication**: Direct agent-to-agent messaging
- **Workflow Patterns**: Sequential, parallel, and synthesis patterns

### **Production Patterns**

Your system demonstrates:
- **Scalability**: Serverless Azure Container Apps deployment
- **Observability**: Full tracing with Application Insights
- **Flexibility**: Easy to add new agents and tools
- **Reliability**: Managed execution with Azure AI Agents Service

### **Next Steps**

Continue exploring:
- **Add More Agents**: Expand with transportation, entertainment specialists
- **Custom Tools**: Build domain-specific MCP tools
- **Advanced Workflows**: Implement conditional branching, loops
- **Production Features**: Add authentication, rate limiting, monitoring

You now have the foundation to build sophisticated AI agent systems that combine the reasoning power of LLMs with structured orchestration and external tool integration.

**Happy coding at Microsoft Ignite 2025!**