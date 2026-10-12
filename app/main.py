from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import auth, bookings, events, payments, users

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Users"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Me"])
app.include_router(bookings.router, prefix="/api/v1", tags=["Bookings"])
app.include_router(payments.router, prefix="/api/v1/bookings", tags=["Payments"])

origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers["X-Content-Type-Options"] = "nosniff"

    if "Referrer-Policy" not in response.headers:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.hostname not in ("localhost", "127.0.0.1"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )

    return response
