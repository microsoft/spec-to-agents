# Spec-to-Agent

> [!WARNING]
> **Work in Progress**: This project is under active development and subject to heavy changes. It is not recommended for testing or production use at this time.

This sample showcases how to generate and orchestrate agents (aided by [spec-kit](https://github.com/github/spec-kit/tree/main)) using **[Microsoft Agent Framework](https://github.com/microsoft/agent-framework)**, it combines the best of:

- **Semantic Kernel**: Enterprise-ready AI orchestration
- **AutoGen**: Multi-agent conversation patterns

The sample is built around an engaging event planning scenario. It demonstrates concurrent workflow execution and real-time workflow visualization.

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
4. **Interactive Frontend**: Visual representation of agent interactions and workflows with [DevUI](https://github.com/microsoft/agent-framework/tree/main/python/packages/devui)
5. **Azure Integration**: Full AZD template deployment to Azure Container Apps

# 🏗️ Architecture Overview

## Core Components
- **Microsoft Agent Framework**: Comprehensive multi-language framework for building, orchestrating, and deploying AI agents with support for both .NET and Python
- **DevUI**: Interactive UI showing real-time agent orchestration inspired by DevUI in Agent Framework
- **Concurrent Workflows**: Demonstrates the workflows functionality for orchestrating complex agentic systems
- **Azure Deployment**: Complete AZD template for one-click deployment

# 🚀 Getting Started

## Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- Azure subscription with appropriate permissions
- Node.js 18+ and npm

## Quick Start with Azure Developer CLI

The easiest way to deploy this sample is using `azd`:

```bash
# Clone the repository
git clone https://github.com/microsoft/spec-to-agents.git
cd spec-to-agents

# Authenticate with Azure
azd auth login

# Initialize and deploy everything
azd up
```

When prompted:
- **Environment name**: Choose a name (e.g., `dev`, `prod`)
- **Azure location**: Choose from `eastus2`, `westus`, `westus2`, `westus3`, `eastus`, `uksouth`, `swedencentral`, `australiaeast`, or `japaneast`
- **Azure subscription**: Select your subscription

**What `azd up` does:**
- Provisions Azure resources (AI Foundry, Cosmos DB, Storage, App Services, etc.)
- Builds and deploys the backend API
- Builds and deploys the frontend application
- Configures all connections and settings

**Alternative commands:**
```bash
# Just provision infrastructure
azd provision

# Just deploy apps (after provisioning)
azd deploy

# View deployed endpoints
azd show

# Set environment variables
azd env set AZURE_LOCATION eastus2
```

## Running Locally

Follow the development setup instructions [here](./DEV_SETUP.md).

**Note:** Local development requires an Azure AI Foundry project and Azure OpenAI deployment. Update `backend/.env` with your Azure credentials.


# 🛠️ Development

## Key Technologies
- **Backend**: Python 3.13, FastAPI for High Performance ASGI Server
- **Frontend**: Vite frontend based on Microsoft Agent Framework DevUI
- **Infrastructure**: Azure Container Apps, AZD template
- **AI**: Azure OpenAI, Microsoft Agent Framework

## Development Workflow

1. **Spec-First**: Define agent specifications and capabilities using spec-kit.
2. **Agent Generation**: Create agents from specifications using the framework
3. **Orchestration**: Implement concurrent workflow and coordination patterns
4. **Visualization**: Build interactive frontend to show agent interactions
5. **Deployment**: Use AZD for one-click Azure deployment

# 🧪 Testing

## Running Tests

```bash
cd tests
uv run pytest
```

# 📦 Infrastructure

The infrastructure is defined in the `infra/` directory using Azure Bicep templates. It includes:

- **Azure AI Foundry**: AI Account and Project for agent orchestration
- **Azure Cosmos DB**: NoSQL database for agent state and memory
- **Azure Storage**: Blob storage for artifacts and data
- **Azure AI Search**: Vector search capabilities
- **Azure App Services**: Hosting for backend API and frontend
- **Azure Application Insights**: Monitoring and telemetry

All resources are provisioned automatically when you run `azd provision` or `azd up`.

# 🤝 Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA).

# 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

