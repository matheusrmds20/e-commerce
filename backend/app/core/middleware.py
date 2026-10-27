from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

NO_STORE_PREFIXES = ("/api/v1/auth", "/api/v1/payments")

CSP_API = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path: str = scope["path"]
        is_api = path.startswith("/api/")
        no_store = path.startswith(NO_STORE_PREFIXES)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)

                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Referrer-Policy", "no-referrer")
                headers.setdefault(
                    "Permissions-Policy",
                    "geolocation=(), microphone=(), camera=()",
                )

                if is_api:
                    headers.setdefault("Content-Security-Policy", CSP_API)

                if scope.get("scheme") == "https":
                    headers.setdefault(
                        "Strict-Transport-Security",
                        "max-age=31536000; includeSubDomains",
                    )

                if no_store:
                    headers.setdefault("Cache-Control", "no-store")
                    headers.setdefault("Pragma", "no-cache")

                if "server" in headers:
                    del headers["server"]

            await send(message)

        await self.app(scope, receive, send_with_headers)
