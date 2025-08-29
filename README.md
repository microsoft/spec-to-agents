# Spec-to-Agent Sample

> ⚠️ **This project is under active development and is a work in progress. Features, APIs, and documentation are subject to change.**

This sample showcases how to generate and orchestrate agents from specifications using Microsoft's new Agent Framework. Built around an engaging event planning scenario, it demonstrates group chat coordination, multi-agent collaboration, and real-time workflow visualization.

## 🎯 Project Overview

**Spec2Agent** is the hero sample for Microsoft Agent Framework - a converged orchestration framework combining the best of Semantic Kernel and AutoGen. This sample demonstrates how to generate agents from specifications and orchestrate them in complex, real-world scenarios.

### What This Sample Demonstrates

1. **Spec-to-Agent Generation**: Create specialized agents from specifications
2. **Event Planning Orchestration**: Comprehensive event planning with multiple collaborating agents
3. **Group Chat Coordination**: Real-time agent collaboration and communication
4. **Interactive Frontend**: Visual representation of agent interactions and workflows
5. **Azure Integration**: Full AZD template deployment to Azure Container Apps

## 🏗️ Architecture Overview

### Core Components
- **Python Backend**: FastAPI application with Microsoft Agent Framework integration
- **TypeScript Frontend**: Interactive UI showing real-time agent orchestration
- **Event Planning Orchestrator**: Demonstrates group chat and multi-agent coordination
- **Azure Deployment**: Complete AZD template for one-click deployment
- **Agent Framework Abstractions**: Showcases the converged Semantic Kernel + AutoGen framework

### Sample Features

🤖 **Spec-to-Agent Generation**: Generate specialized agents from specifications  
🎭 **Event Planning Orchestration**: Multi-agent collaboration for complex event planning  
💬 **Group Chat Coordination**: Real-time agent communication and decision-making  
📊 **Visual Workflow**: Interactive frontend showing agent interactions  
☁️ **Azure Integration**: Deploy with `azd up` to Azure Container Apps  

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+
- Azure CLI with AZD extension
- Azure subscription

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/microsoft/spec-to-agents.git
   cd spec-to-agents
   ```

2. **Deploy to Azure (Recommended)**
   ```bash
   azd up
   ```
   This will provision all Azure resources and deploy both backend and frontend.

3. **Or run locally**
   ```bash
   # Backend
   cd src/backend
   uv venv                    # Create virtual environment
   uv sync                    # Install dependencies
   uv run python app/main.py  # Run the FastAPI server
   
   # Frontend (separate terminal)
   cd src/frontend
   npm install
   npm run dev
   ```

## 🎭 Event Planning Sample

### The Scenario
Plan a comprehensive corporate event using multiple specialized agents working together in real-time.

### Meet the Agents
- **Event Coordinator**: Orchestrates the overall planning process
- **Venue Specialist**: Researches and recommends venues
- **Budget Analyst**: Manages costs and financial constraints
- **Catering Coordinator**: Handles food and beverage planning
- **Logistics Manager**: Coordinates schedules and resources

### How It Works
1. **Spec Generation**: Define your event requirements
2. **Agent Creation**: Agents are generated from specifications
3. **Group Chat**: Watch agents collaborate in real-time
4. **Decision Making**: See how agents reach consensus
5. **Final Plan**: Get a comprehensive event plan

### Try the Sample
Visit the frontend after deployment to:
- Input event specifications
- Watch agents collaborate in group chat
- See real-time workflow visualization
- Download the final event plan

## 🛠️ Development

### Project Structure
```
spec-to-agents/
├── azure.yaml              # AZD configuration
├── .github/                 # CI/CD workflows
├── infra/                   # Bicep infrastructure templates
├── src/
│   ├── backend/            # Python FastAPI backend
│   │   ├── app/
│   │   │   ├── agents/     # Agent generation and orchestration
│   │   │   ├── api/        # REST API endpoints
│   │   │   └── core/       # Configuration and models
│   │   └── requirements.txt
│   └── frontend/           # TypeScript React frontend
│       ├── src/
│       │   ├── components/ # UI components
│       │   ├── services/   # API integration
│       │   └── views/      # Page views
│       └── package.json
└── README.md
```

### Key Technologies
- **Backend**: Python 3.13, FastAPI, Microsoft Agent Framework
- **Frontend**: TypeScript, React, Real-time WebSocket integration
- **Infrastructure**: Azure Container Apps, AZD template
- **AI**: Azure OpenAI, Microsoft Agent Framework (Semantic Kernel + AutoGen)

### Development Workflow

1. **Spec-First**: Define agent specifications and capabilities
2. **Agent Generation**: Create agents from specifications using the framework
3. **Orchestration**: Implement group chat and coordination patterns
4. **Visualization**: Build interactive frontend to show agent interactions
5. **Deployment**: Use AZD for one-click Azure deployment

## 🧪 Testing

### Running Tests
```bash
# Backend tests
cd src/backend
uv run pytest

# Frontend tests
cd src/frontend
npm test

# End-to-end tests
npm run test:e2e
```

## 🚀 Deployment

### One-Click Azure Deployment
```bash
azd up
```

This AZD template provisions and deploys:
- **Azure Container Apps**: Hosts both backend and frontend
- **Azure Container Registry**: Stores container images
- **Azure OpenAI**: Powers the AI agents
- **CosmosDB**: Document database for state persistence
- **Application Insights**: Monitoring and diagnostics
- **Key Vault**: Secure secrets management

### Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │  Azure OpenAI   │
│  (React/TS)     │◄──►│  (FastAPI/Py)    │◄──►│   (Agents)      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │     Azure Container Apps    │
                    │    (Managed Environment)    │
                    └────────────────────────────┘
```

## 🤖 Microsoft Agent Framework

This sample showcases **Microsoft Agent Framework** - the new unified orchestration framework that combines the best of:

- **Semantic Kernel**: Enterprise-ready AI orchestration
- **AutoGen**: Multi-agent conversation patterns

### Key Framework Features Demonstrated
- **Group Chat**: Multi-agent real-time collaboration
- **Agent Generation**: Create agents from specifications
- **Orchestration Patterns**: Advanced coordination and workflow management
- **Tool Integration**: Seamless tool and API integration
- **Human-in-the-Loop**: Interactive approval and feedback workflows

## 🤝 Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ready to see agents in action?** Deploy with `azd up` and watch the event planning orchestration come to life!
