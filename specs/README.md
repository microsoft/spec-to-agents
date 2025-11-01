# Unified Specifications

## Overview

This document outlines the specifications for the unified components of the project, i.e., changes that affect both the frontend and backend. It serves as a guide for developers to understand the architecture, technology stack, and development guidelines.

## Specs

- [Event Planning Workflow](workflow-skeleton.md) - Complete multi-agent workflow with coordinator-centric star topology, service-managed threads, structured output routing, and human-in-the-loop support. **Status: ✅ Implemented**
- [Agent Tools Integration](agent-tools.md) - Comprehensive specification for integrating custom Web Search, Weather (Open-Meteo), Calendar (iCalendar), Code Interpreter, and MCP sequential-thinking-tools with Azure AI Foundry agents. **Status: ✅ Implemented**

## Key Implementation Patterns

The workflow uses these framework patterns (documented in specs above):

1. **Service-Managed Threads** (`store=True`): Automatic conversation history management via Azure AI service
2. **Tool Content Conversion**: Convert tool calls/results to text summaries for cross-thread communication
3. **HITL Checkpointing**: Framework-native `ctx.request_info()` + `@response_handler` for user interaction
4. **Structured Output Routing**: Pydantic `SpecialistOutput` model with `next_agent` field for dynamic routing
5. **Coordinator-Centric Star Topology**: Central hub executor managing all routing between specialists