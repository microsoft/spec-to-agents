# Spec-to-Agent

This sample showcases how to generate and orchestrate agents (aided by [spec-kit](https://github.com/github/spec-kit/tree/main)) using **Microsoft Agent Framework**--the new unified orchestration framework that combines the best of:

- **Semantic Kernel**: Enterprise-ready AI orchestration
- **AutoGen**: Multi-agent conversation patterns

Built around an engaging event planning scenario, it demonstrates concurrent workflow execution and real-time workflow visualization.

# 🎯 Project Overview

## 🎭 Event Planning Sample

### The Scenario
Plan a comprehensive event using multiple specialized agents working together.

### Meet the Agents
- **Event Coordinator**: Orchestrates the overall planning process
- **Venue Specialist**: Researches and recommends venues
- **Budget Analyst**: Manages costs and financial constraints
- **Catering Coordinator**: Handles food and beverage planning
- **Logistics Manager**: Coordinates schedules and resources

### What This Sample Demonstrates

1. **Spec-to-Agent Generation**: Create specialized agents by using spec-driven development with [spec-kit](https://github.com/github/spec-kit/tree/main)
2. **Event Planning Orchestration**: Comprehensive event planning with multiple collaborating agents
3. **Concurrent Workflows**: Agent orchestration with parallel execution paths and fan-in/fan-out patterns
4. **Interactive Frontend**: Visual representation of agent interactions and workflows for optimizing user experience
5. **Azure Integration**: Full AZD template deployment to Azure Container Apps

# 🏗️ Architecture Overview

## Core Components
- **Agent Framework**: Showcases the converged Semantic Kernel + AutoGen framework, Microsoft Agent Framework, with integration using the Python SDK
- **DevUI**: Interactive UI showing real-time agent orchestration inspired by DevUI in Agent Framework
- **Concurrent Workflows**: Demonstrates the workflows functionality for orchestrating complex agentic systems
- **Azure Deployment**: Complete AZD template for one-click deployment

# 🚀 Getting Started

## Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Azure CLI with AZD extension
- Azure subscription

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/microsoft/spec-to-agents.git
   ```

2. **Deploy to Azure (Recommended)**
   ```bash
   azd up
   ```
   This will provision all Azure resources and deploy both backend and frontend.

3. **Or run locally**
   ```bash
   # Terminal 1 - Start backend
   cd backend
   uv sync  # Install dependencies (first time only)
   uv run app/main.py

   # Terminal 2 - Start frontend
   cd frontend
   npm install
   npm run dev
   ```

   Then open your browser to `http://localhost:5173`


# 🛠️ Development

## Key Technologies
- **Backend**: Python 3.13, FastAPI for High Performance ASGI Server
- **Frontend**: Vite frontend based on Microsoft Agent Framework DevUI
- **Infrastructure**: Azure Container Apps, AZD template
- **AI**: Azure OpenAI, Microsoft Agent Framework (Semantic Kernel + AutoGen)

## Development Workflow

1. **Spec-First**: Define agent specifications and capabilities using spec-kit.
2. **Agent Generation**: Create agents from specifications using the framework
3. **Orchestration**: Implement concurrent workflow and coordination patterns
4. **Visualization**: Build interactive frontend to show agent interactions
5. **Deployment**: Use AZD for one-click Azure deployment

# 🧪 Testing

## Running Tests

```bash
# Backend tests
cd src/backend
uv run pytest

# Frontend tests
cd src/frontend
npm install
npm run test
```

# 🚀 Deployment

## One-Click Azure Deployment
```bash
azd up
```

# 🤝 Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA).

# 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

