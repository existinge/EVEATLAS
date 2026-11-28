"""ATLAS provider adapters. Opt-in only; stdlib HTTP; no keys in the repository.

The OpenClaw gateway provider is enabled only when ATLAS_ENABLE_OPENCLAW=1 (or the
CLI flag --enable-openclaw) AND ATLAS_OPENCLAW_URL, ATLAS_OPENCLAW_TOKEN,
ATLAS_OPENCLAW_MODEL and both price env vars are set. Prices are never assumed:
they bound the cost reservation and convert gateway-reported usage into a charge.
"""
import json
import math
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

LOOPBACK = {"127.0.0.1", "localhost", "::1"}
DEFAULT_MAX_TOKENS = 512
MAX_TOKENS_LIMIT = 8192

class ProviderError(RuntimeError):
    """Raised when a provider call fails. `billable_unknown` is True when the
    request may have reached the provider, so the charge must stay uncertain."""
    def __init__(self, message, billable_unknown=True):
        super().__init__(message)
        self.billable_unknown = billable_unknown

def _price(value, name):
    try:
        p = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"{name} must be a decimal USD amount per 1M tokens") from exc
    if not p.is_finite() or p <= 0:
        raise ValueError(f"{name} must be positive")
    return p

class Provider:
    """Interface: name, model, estimate_max_cost(prompt, max_tokens) -> Decimal USD,
    cost(input_tokens, output_tokens) -> Decimal USD, complete(prompt, max_tokens) -> dict."""
    name = "provider"
    model = "unknown"
    def __init__(self, input_usd_per_mtok, output_usd_per_mtok):
        self.input_price = _price(input_usd_per_mtok, "input price")
        self.output_price = _price(output_usd_per_mtok, "output price")
    def cost(self, input_tokens, output_tokens):
        return (Decimal(input_tokens) * self.input_price + Decimal(output_tokens) * self.output_price) / Decimal(1_000_000)
    def estimate_max_cost(self, prompt, max_tokens):
        # Conservative bound: assume <= 1 token per character of prompt plus overhead.
        return self.cost(len(prompt) + 64, max_tokens)
    def complete(self, prompt, max_tokens):
        raise NotImplementedError

class OpenClawProvider(Provider):
    """OpenAI-style chat completions via a local OpenClaw gateway.
    ATLAS holds only a scoped gateway token; model provider keys stay in the gateway."""
    name = "openclaw"
    def __init__(self, token, base_url, model, input_usd_per_mtok, output_usd_per_mtok, timeout=60, opener=None):
        super().__init__(input_usd_per_mtok, output_usd_per_mtok)
        if not token: raise ValueError("ATLAS_OPENCLAW_TOKEN is required")
        if not model: raise ValueError("ATLAS_OPENCLAW_MODEL is required")
        self.base_url = validate_gateway_url(base_url)
        self._token, self.model, self.timeout = token, model, timeout
        self._open = opener or urllib.request.urlopen
    def __repr__(self):  # never expose the token
        return f"OpenClawProvider(model={self.model!r}, base_url={self.base_url!r})"
    def build_request(self, prompt, max_tokens):
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens, "stream": False}
        return urllib.request.Request(self.base_url + "/v1/chat/completions", data=json.dumps(body).encode(),
                                      method="POST", headers={"Content-Type": "application/json",
                                                              "Authorization": "Bearer " + self._token})
    def complete(self, prompt, max_tokens):
        req = self.build_request(prompt, max_tokens)
        try:
            with self._open(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # 4xx (auth/validation) is treated as rejected before generation; 5xx may have been billed upstream.
            raise ProviderError(f"openclaw gateway HTTP {exc.code}", billable_unknown=exc.code >= 500) from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise ProviderError(f"openclaw gateway request failed: {type(exc).__name__}") from None
        try:
            text = payload["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise ProviderError("openclaw gateway response missing content") from None
        tin = tout = None
        usage = payload.get("usage")
        if isinstance(usage, dict):
            a, b = usage.get("prompt_tokens"), usage.get("completion_tokens")
            if type(a) is int and type(b) is int and a >= 0 and b >= 0:
                tin, tout = a, b
        return {"text": text, "input_tokens": tin, "output_tokens": tout, "model": payload.get("model", self.model)}

def validate_gateway_url(raw):
    """Require an explicit URL with a port; plain HTTP only on loopback."""
    if not raw: raise ValueError("ATLAS_OPENCLAW_URL is required (e.g. http://127.0.0.1:<gateway-port>)")
    parts = urllib.parse.urlsplit(raw.strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("ATLAS_OPENCLAW_URL must be http(s)://host:port without credentials")
    if parts.port is None: raise ValueError("ATLAS_OPENCLAW_URL must include the gateway port; none is assumed")
    if parts.scheme == "http" and parts.hostname not in LOOPBACK:
        raise ValueError("plain HTTP is allowed only for a loopback gateway")
    if parts.path not in {"", "/"} or parts.query or parts.fragment:
        raise ValueError("ATLAS_OPENCLAW_URL must be the gateway base URL only")
    return f"{parts.scheme}://{parts.netloc}"

class FakeProvider(Provider):
    """Deterministic offline provider for tests. `replies` are strings or exceptions."""
    def __init__(self, replies, name="openclaw", model="fake-model", input_usd_per_mtok="1", output_usd_per_mtok="2",
                 input_tokens=100, output_tokens=50):
        """Set input_tokens/output_tokens to None to simulate a gateway that reports no usage."""
        super().__init__(input_usd_per_mtok, output_usd_per_mtok)
        self.name, self.model, self.replies, self.calls = name, model, list(replies), []
        self.input_tokens, self.output_tokens = input_tokens, output_tokens
    def complete(self, prompt, max_tokens):
        self.calls.append({"prompt": prompt, "max_tokens": max_tokens})
        reply = self.replies.pop(0) if self.replies else ProviderError("fake provider exhausted", False)
        if isinstance(reply, Exception): raise reply
        return {"text": reply, "input_tokens": self.input_tokens, "output_tokens": self.output_tokens, "model": self.model}

def configured_providers(env, enable_openclaw=False):
    """Return {name: provider} for adapters that are explicitly enabled and fully configured."""
    providers = {}
    if enable_openclaw or env.get("ATLAS_ENABLE_OPENCLAW") == "1":
        names = ["ATLAS_OPENCLAW_URL", "ATLAS_OPENCLAW_TOKEN", "ATLAS_OPENCLAW_MODEL",
                 "ATLAS_OPENCLAW_INPUT_USD_PER_MTOK", "ATLAS_OPENCLAW_OUTPUT_USD_PER_MTOK"]
        missing = [n for n in names if not env.get(n)]
        if missing: raise ValueError("OpenClaw enabled but missing env: " + ", ".join(missing))
        providers["openclaw"] = OpenClawProvider(env["ATLAS_OPENCLAW_TOKEN"], env["ATLAS_OPENCLAW_URL"],
                                                 env["ATLAS_OPENCLAW_MODEL"], env["ATLAS_OPENCLAW_INPUT_USD_PER_MTOK"],
                                                 env["ATLAS_OPENCLAW_OUTPUT_USD_PER_MTOK"])
    return providers

def max_tokens_for(spec):
    n = spec.get("max_tokens", DEFAULT_MAX_TOKENS)
    if type(n) is not int or not 1 <= n <= MAX_TOKENS_LIMIT:
        raise ValueError(f"max_tokens must be an integer 1..{MAX_TOKENS_LIMIT}")
    return n

def cost_cents_ceiling(usd):
    return max(1, math.ceil(usd * 100))
