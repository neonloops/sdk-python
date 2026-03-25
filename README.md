# neonloops

Python SDK for [Neonloops](https://neonloops.com) — run AI workflows via API.

## Installation

```bash
pip install neonloops
```

## Quick Start

### Async (recommended)

```python
import asyncio
from neonloops import Runner, RunInput

runner = Runner(
    api_key="nl_sk_...",
    # base_url="https://neonloops.com",  # optional, defaults to https://neonloops.com
)

async def main():
    result = await runner.run(
        workflow_id="wf_abc123",
        input=[RunInput(role="user", content="Hello, run my workflow!")],
    )
    print(result.output)
    print(result.metadata.tokens)

asyncio.run(main())
```

### Sync

```python
from neonloops import Runner, RunInput

runner = Runner(
    api_key="nl_sk_...",
    # base_url="https://neonloops.com",  # optional, defaults to https://neonloops.com
)

result = runner.run_sync(
    workflow_id="wf_abc123",
    input=[RunInput(role="user", content="Hello!")],
)
print(result.output)
```

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | — | **Required.** Your Neonloops API key (`nl_sk_...`) |
| `base_url` | `str` | `https://neonloops.com` | Base URL of your Neonloops instance |
| `project_id` | `str` | `None` | Default project ID to scope requests |
| `timeout` | `float` | `120.0` | Request timeout in seconds |
| `max_retries` | `int` | `2` | Max retries for 429/5xx errors |

## Multi-Turn Conversations

```python
# Create a session
session = await runner.create_session("wf_abc123")

# First turn
r1 = await runner.run(
    workflow_id="wf_abc123",
    input=[RunInput(role="user", content="Hello!")],
    session_id=session.id,
)

# Follow-up — server loads previous messages automatically
r2 = await runner.run(
    workflow_id="wf_abc123",
    input=[RunInput(role="user", content="Tell me more")],
    session_id=session.id,
)

# Retrieve message history
messages = await runner.get_session_messages(session.id)
```

## Error Handling

```python
from neonloops import Runner, NeonloopsApiError, NeonloopsTimeoutError

try:
    result = await runner.run(
        workflow_id="wf_abc123",
        input=[RunInput(role="user", content="Hello")],
    )
except NeonloopsApiError as e:
    print(f"API error {e.status}: {e}")
except NeonloopsTimeoutError as e:
    print(f"Timeout: {e}")
```

## License

MIT
