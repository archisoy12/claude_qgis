from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from auth import authenticate, create_token, require_any
from schemas import LoginRequest, TokenResponse
from routers import centers, tenants, leases, vacancy, transactions, upload

app = FastAPI(title="물류센터 데이터 플랫폼", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(centers.router,      prefix="/api/centers",      tags=["centers"])
app.include_router(tenants.router,      prefix="/api/tenants",      tags=["tenants"])
app.include_router(leases.router,       prefix="/api/leases",       tags=["leases"])
app.include_router(vacancy.router,      prefix="/api/vacancy",      tags=["vacancy"])
app.include_router(transactions.router, prefix="/api/transactions",  tags=["transactions"])
app.include_router(upload.router,       prefix="/api/upload",        tags=["upload"])


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    from fastapi import HTTPException, status
    role = authenticate(body.password)
    if not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 올바르지 않습니다.")
    return TokenResponse(access_token=create_token(role), role=role)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# 프론트엔드 정적 파일 서빙
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
