# FlowForge

FlowForge is an intelligent automation platform MVP built around a Python async workflow engine and a React visual workflow builder.

## Features

- FastAPI + SQLAlchemy async backend
- PostgreSQL persistence
- Redis event broker
- Async DAG-style workflow execution
- Webhook triggers
- HTTP, AI, condition, transform, delay, notification and database nodes
- Retry with exponential backoff
- Real-time execution events over WebSockets
- JWT authentication
- React + React Flow visual editor
- Premium dark UI with responsive states
- Docker Compose development stack

## Run

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Open `http://localhost:5173` and create an account. The dashboard can generate a demo workflow.

API docs: `http://localhost:8000/docs`

## Demo webhook

After creating and enabling a workflow, POST JSON to:

`http://localhost:8000/api/webhooks/<workflow_id>`

## Notes

The AI node intentionally has a deterministic local fallback so the complete demo works without an API key. Configure `OPENAI_API_KEY` to replace the fallback with a production provider implementation.

This is an MVP foundation. For production, move task execution from FastAPI process memory to a durable worker/queue architecture, add encrypted credential storage, migrations, rate limiting, and more integration adapters.
