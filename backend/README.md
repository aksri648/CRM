# Xeno AI Campaign Studio — Backend

Three-microservice architecture for an AI-Native Marketing Platform.

## Architecture

### App Service (port 8001)
- Main backend — source of truth for all business data
- Customer, order, product, segment, campaign management
- Authentication (JWT), RBAC, approval workflows
- Analytics engine, scheduler, Telegram bot integration
- Orchestrates Agent Service and Communication Service

### Agent Service (port 8002)
- Pure LangGraph multi-agent system — NO database, NO models
- 9 specialized AI agents: Athena, Atlas, Sophia, Mercury, Nova, Darwin, Orion, Apollo, Sentinel
- Campaign generation and opportunity discovery graphs
- Stateless — receives goals, returns proposals

### Communication Service (port 8003)
- Pure channel engine — NO AI, NO LangGraph, NO OpenAI
- Campaign dispatch, message scheduling, queue processing
- Delivery lifecycle simulation (event sourcing)
- Retry logic, dead letter queues
- Callbacks to App Service for analytics updates

## Communication Patterns

- **Synchronous**: App → Agent (HTTP, campaign generation), App → Comm (HTTP, dispatch)
- **Asynchronous**: Comm → App (HTTP callback, event updates)
- **No direct communication**: Agent ↔ Comm never talk directly

## Quick Start

```bash
docker compose up -d
docker compose run --rm seed
# App Service:      http://localhost:8001
# Agent Service:    http://localhost:8002
# Communication:    http://localhost:8003
```

## Demo Flow

1. Generate campaign: POST /api/v1/agents/generate-campaign
2. View approvals: GET /api/v1/approvals
3. Approve: POST /api/v1/approvals/{id}/respond
4. Launch: POST /api/v1/campaigns/{id}/launch (dispatches to Comm Service)
5. Analytics: GET /api/v1/campaigns/{id}/performance
