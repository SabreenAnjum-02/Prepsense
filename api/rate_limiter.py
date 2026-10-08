import time
from collections import defaultdict
from fastapi import Request
from starlette.responses import JSONResponse

class SimpleRateLimiter:
    """
    A lightweight, in-memory rate limiter to protect sensitive endpoints 
    like /auth/login from brute-force attacks.
    """
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        
    async def __call__(self, request: Request, call_next):
        # We only rate limit specific paths, e.g., auth or session creation
        path = request.url.path
        if "/auth" in path or "/start" in path:
            client_ip = request.client.host if request.client else "unknown"
            
            now = time.time()
            # Clean up old requests
            self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]
            
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."}
                )
                
            self.requests[client_ip].append(now)
            
        return await call_next(request)

rate_limiter = SimpleRateLimiter(requests_per_minute=20)
