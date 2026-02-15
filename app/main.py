from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.routers import auth, users, courses, enrollments
import app.models.user, app.models.course, app.models.enrollment, app.models.audit
from app.utils.rate_limit import limiter

app = FastAPI(title="Course Enrollment Platform")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(enrollments.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
