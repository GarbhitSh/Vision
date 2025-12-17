"""
VISION Master Node - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import socketio

from config.settings import settings
from config.database import init_db
from api.routes import frames, analytics, alerts, zones, cameras, dashboard, streaming, cross_camera
from api.websocket import router as websocket_router
from api.socketio_handler import setup_socketio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI app"""
    # Startup
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="VISION Master Node API",
    description="AI-Powered Crowd Monitoring & Safety System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(frames.router, prefix="/api/v1", tags=["frames"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(zones.router, prefix="/api/v1", tags=["zones"])
app.include_router(cameras.router, prefix="/api/v1", tags=["cameras"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(streaming.router, tags=["streaming"])
app.include_router(cross_camera.router, prefix="/api/v1", tags=["cross-camera"])

# Include WebSocket router
app.include_router(websocket_router)

# Setup Socket.IO
setup_socketio(app)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected",
        "timestamp": "2024-01-01T12:00:00Z"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VISION Master Node API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

