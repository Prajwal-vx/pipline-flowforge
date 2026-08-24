from dataclasses import dataclass, field
from typing import Any
import asyncio
import ipaddress
import socket
from urllib.parse import urlparse
import httpx

@dataclass
class NodeContext:
    execution_id: str
    node_id: str
    data: dict[str, Any] = field(default_factory=dict)

class BaseNode:
    type_name = "base"
    async def run(self, config: dict, ctx: NodeContext) -> dict:
        raise NotImplementedError

async def validate_outbound_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Outbound URL must be an HTTP(S) URL without embedded credentials")
    try:
        addresses = await asyncio.to_thread(socket.getaddrinfo, parsed.hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Outbound URL hostname could not be resolved") from exc
    for address in {item[4][0] for item in addresses}:
        ip = ipaddress.ip_address(address)
        if any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_multicast, ip.is_reserved, ip.is_unspecified)):
            raise ValueError("Outbound URL must resolve to a public address")
    return value

class TriggerNode(BaseNode):
    type_name = "trigger"
    async def run(self, config, ctx):
        return {"trigger": ctx.data.get("input", {})}

class HTTPNode(BaseNode):
    type_name = "http"
    async def run(self, config, ctx):
        method = str(config.get("method", "GET")).upper()
        url = config.get("url")
        if not url:
            raise ValueError("HTTP node requires a URL")
        await validate_outbound_url(url)
        timeout = float(config.get("timeout", 15))
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.request(method, url, headers=config.get("headers") or {}, params=config.get("params") or {}, json=config.get("body"))
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            body = response.json() if "application/json" in content_type else response.text
            return {"status_code": response.status_code, "body": body}

class ConditionNode(BaseNode):
    type_name = "condition"
    async def run(self, config, ctx):
        left = config.get("left")
        op = config.get("operator", "equals")
        right = config.get("right")
        if isinstance(left, str) and left.startswith("{{") and left.endswith("}}"):
            path = left[2:-2].strip().split(".")
            current = ctx.data
            for key in path:
                if isinstance(current, dict):
                    current = current.get(key)
                else:
                    current = None
                    break
            left = current
        if op == "equals": value = left == right
        elif op == "not_equals": value = left != right
        elif op == "contains": value = right in left if left is not None else False
        elif op == "greater_than": value = left > right
        elif op == "less_than": value = left < right
        elif op == "exists": value = left is not None
        else: raise ValueError(f"Unknown condition operator: {op}")
        return {"result": bool(value)}

class TransformNode(BaseNode):
    type_name = "transform"
    async def run(self, config, ctx):
        import json
        mode = config.get("mode", "merge")
        data = config.get("data") or {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise ValueError("Transform data must be valid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Transform data must be a JSON object")
        if mode == "pick":
            return {key: ctx.data.get(key) for key in config.get("fields", [])}
        if mode == "merge":
            result = dict(ctx.data)
            result.update(data)
            return result
        raise ValueError(f"Unsupported transform mode: {mode}")

class DelayNode(BaseNode):
    type_name = "delay"
    async def run(self, config, ctx):
        import asyncio
        await asyncio.sleep(min(float(config.get("seconds", 1)), 300))
        return {"delayed_seconds": float(config.get("seconds", 1))}

class NotificationNode(BaseNode):
    type_name = "notification"
    async def run(self, config, ctx):
        provider = config.get("provider", "discord")
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Notification requires webhook_url")
        await validate_outbound_url(webhook_url)
        payload = {"content": str(config.get("message", "FlowForge notification"))}
        if provider == "slack":
            payload = {"text": payload["content"]}
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            r = await client.post(webhook_url, json=payload)
            r.raise_for_status()
        return {"sent": True, "provider": provider, "status_code": r.status_code}

class AINode(BaseNode):
    type_name = "ai"
    async def run(self, config, ctx):
        prompt = config.get("prompt", "Analyze this workflow data")
        if not ctx.data:
            return {"analysis": "No input data"}
        # Deterministic local fallback keeps the demo runnable without a provider key.
        if not __import__("os").getenv("OPENAI_API_KEY"):
            text = str(ctx.data).lower()
            priority = "high" if any(x in text for x in ["urgent", "critical", "refund", "failed"]) else "normal"
            sentiment = "negative" if any(x in text for x in ["bad", "angry", "error", "failed"]) else "neutral"
            return {"analysis": {"priority": priority, "sentiment": sentiment, "reason": "local rule-based fallback"}}
        return {"analysis": {"priority": "normal", "sentiment": "neutral", "reason": "provider integration placeholder"}}

class DatabaseNode(BaseNode):
    type_name = "database"
    async def run(self, config, ctx):
        # Demo-safe node: returns the operation payload. Production adapters can persist through SQLAlchemy.
        return {"operation": config.get("operation", "insert"), "table": config.get("table", "workflow_events"), "data": ctx.data}

NODE_REGISTRY = {c.type_name: c for c in [TriggerNode, HTTPNode, ConditionNode, TransformNode, DelayNode, NotificationNode, AINode, DatabaseNode]}
