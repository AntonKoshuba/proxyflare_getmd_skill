import random
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from js import Object, Response, fetch
from pyodide.ffi import to_js

FILTERED_PARAMS = frozenset({"url", "_cb", "_t"})


def generate_random_ip() -> str:
    """Generate a random IP for X-Forwarded-For anonymization."""
    return ".".join(str(random.randint(1, 255)) for _ in range(4))  # noqa: S311


def create_error_response(
    message: str,
    details: dict[str, Any] | None = None,
    status: int = 500,
    cors_headers: dict[str, str] | None = None,
) -> Response:
    body = {"error": message}
    if details:
        body.update(details)

    headers = {
        "Content-Type": "application/json",
    }
    # Use provided CORS headers or safe defaults
    if cors_headers:
        headers.update(cors_headers)
    else:
        headers.update(
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                "Access-Control-Allow-Headers": "*",
            }
        )

    # Prepare init object
    init_opts = {
        "status": status,
        "headers": headers,
    }
    init_js = to_js(init_opts, dict_converter=Object.fromEntries)

    # Use Response.json (JS static method).
    # Note: Response.json takes a JS object as data.
    body_js = to_js(body, dict_converter=Object.fromEntries)
    return Response.json(body_js, init_js)


async def on_fetch(request: Any, env: Any) -> Any:
    # 0. Handle CORS preflight
    if request.method == "OPTIONS":
        init_opts = {
            "status": 204,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                "Access-Control-Allow-Headers": "*",
            },
        }
        init_js = to_js(init_opts, dict_converter=Object.fromEntries)
        return Response.new(None, init_js)

    # 1. Parse the target URL
    parsed_url = urlparse(request.url)
    query_params = parse_qs(parsed_url.query)

    # Priority: 1. Query Param, 2. Header, 3. Path
    target_url = None

    # 1.1 Query Param
    url_param = query_params.get("url")
    if url_param and url_param[0]:
        target_url = url_param[0]
        # Rebuild target URL with filtered query params (remove url, _cb, _t)
        target_parsed = urlparse(target_url)
        filtered_qs = {
            k: v for k, v in parse_qs(target_parsed.query).items() if k not in FILTERED_PARAMS
        }
        # Merge original query's non-filtered params onto target
        extra_qs = {k: v for k, v in query_params.items() if k not in FILTERED_PARAMS}
        filtered_qs.update(extra_qs)
        new_query = urlencode(filtered_qs, doseq=True) if filtered_qs else ""
        target_url = urlunparse(target_parsed._replace(query=new_query))

    # 1.2 Header
    if not target_url:
        target_url = request.headers.get("X-Target-URL")

    # 1.3 Path (e.g. /https://example.com)
    if not target_url and parsed_url.path != "/":
        path = parsed_url.path.lstrip("/")
        if path.startswith("http"):
            target_url = path

    if not target_url:
        return create_error_response(
            "Missing target URL",
            details={
                "usage": {
                    "query_param": "?url=https://example.com",
                    "header": "X-Target-URL: https://example.com",
                    "path": "/https://example.com",
                }
            },
            status=400,
        )

    # 2. Prepare headers
    headers = {}
    for key, value in request.headers.entries():
        key_lower = key.lower()
        if key_lower in ("host", "cf-connecting-ip", "cf-ipcountry", "cf-ray", "cf-visitor"):
            continue
        if key_lower == "x-my-x-forwarded-for":
            # Client-provided forwarded IP — pass as X-Forwarded-For
            headers["X-Forwarded-For"] = value
            continue

        # Use original key casing unless it's x-forwarded-for which we might want specific handling
        # But generally, if we want to detect if it exists, we track lower case keys.
        headers[key] = value

    # Check if X-Forwarded-For exists (case-insensitive)
    has_forwarded_for = any(k.lower() == "x-forwarded-for" for k in headers)

    # Set X-Forwarded-For if not provided by client
    if not has_forwarded_for:
        headers["X-Forwarded-For"] = generate_random_ip()

    # 3. Request body
    method = request.method
    body = request.body if method not in ("GET", "HEAD") else None

    # 4. Prepare init options
    init_opts = {"method": method, "headers": headers, "body": body}
    init_js = to_js(init_opts, dict_converter=Object.fromEntries)

    # 5. Fetch and return
    try:
        response = await fetch(target_url, init_js)

        # 6. Process Response Headers
        new_headers = {}
        for key, value in response.headers.entries():
            key_lower = key.lower()
            if key_lower not in ("content-encoding", "content-length", "transfer-encoding"):
                new_headers[key] = value

        # Add CORS
        cors_headers = {
            "Access-Control-Allow-Origin": getattr(env, "CORS_ORIGIN", "*"),
            "Access-Control-Allow-Methods": getattr(env, "CORS_METHODS", "GET, POST, OPTIONS"),
            "Access-Control-Allow-Headers": getattr(env, "CORS_ALLOWED_HEADERS", "*"),
        }
        new_headers.update(cors_headers)

        # Prepare response init
        resp_init = {
            "status": response.status,
            "statusText": response.statusText,
            "headers": new_headers,
        }
        resp_init_js = to_js(resp_init, dict_converter=Object.fromEntries)

        # response.body is a ReadableStream from JS interop — streaming is handled
        # natively by the Cloudflare Python Workers runtime via pyodide.
        return Response.new(response.body, resp_init_js)
    except Exception as e:
        return create_error_response(f"Proxy Error: {str(e)}", status=502)
