"""
Static File Serving Configuration for FastAPI

This module configures FastAPI to serve the built React frontend static files
while preserving API routes and handling Single Page Application (SPA) routing.
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from config.environment import get_settings
from logging_system import get_logger

logger = get_logger(__name__)
settings = get_settings()

def get_frontend_build_path() -> Path:
    """
    Get the path to the frontend build directory.
    
    Returns:
        Path to the frontend dist directory
    """
    # Try multiple possible locations for the frontend build
    possible_paths = [
        Path(__file__).parent.parent / "frontend" / "dist",  # Development structure
        Path(__file__).parent / "static",                    # Production build location
        Path("/app/frontend/dist"),                          # Docker container structure
        Path("./frontend/dist"),                             # Current directory relative
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            logger.info(f"Found frontend build at: {path}")
            return path
    
    # If no build found, create a fallback
    fallback_path = Path(__file__).parent.parent / "frontend" / "dist"
    logger.warning(f"No frontend build found, using fallback: {fallback_path}")
    return fallback_path

def is_api_route(path: str) -> bool:
    """
    Check if a path is an API route that should not be handled by static file serving.
    
    Args:
        path: Request path
        
    Returns:
        True if the path is an API route
    """
    api_prefixes = [
        "/api",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/agents",
        "/jobs",
        "/pipeline",
        "/config",
        "/auth",
        "/adk",
        "/cors-info",
        "/logs",
        # Agent-specific endpoints
        "/text-processing",
        "/summarization", 
        "/web-scraping",
    ]
    
    return any(path.startswith(prefix) for prefix in api_prefixes)

def is_static_asset(path: str) -> bool:
    """
    Check if a path is a static asset (JS, CSS, images, etc.).
    
    Args:
        path: Request path
        
    Returns:
        True if the path is a static asset
    """
    static_extensions = {
        ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", 
        ".ico", ".woff", ".woff2", ".ttf", ".eot", ".map",
        ".json", ".xml", ".txt"
    }
    
    return any(path.endswith(ext) for ext in static_extensions)

class SPAStaticFiles(StaticFiles):
    """
    Custom StaticFiles class that handles Single Page Application routing.
    
    For any request that is not an API route or static asset, it serves the index.html
    file to allow client-side routing to work properly.
    """
    
    async def get_response(self, path: str, scope):
        """
        Get response for a given path, with SPA fallback logic.
        
        Args:
            path: Request path
            scope: ASGI scope
            
        Returns:
            Response object
        """
        try:
            # Try to get the file normally first
            response = await super().get_response(path, scope)
            return response
        except HTTPException as e:
            # If file not found and it's not an API route or static asset,
            # serve index.html for SPA routing
            if e.status_code == 404 and not is_api_route(f"/{path}") and not is_static_asset(path):
                # Serve index.html for client-side routing
                index_path = Path(self.directory) / "index.html"
                if index_path.exists():
                    return FileResponse(
                        index_path,
                        media_type="text/html",
                        headers={
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma": "no-cache",
                            "Expires": "0"
                        }
                    )
            
            # Re-raise the original exception for other cases
            raise e

def configure_static_files(app: FastAPI) -> None:
    """
    Configure static file serving for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    frontend_path = get_frontend_build_path()
    
    if not frontend_path.exists():
        logger.warning(f"Frontend build directory not found at {frontend_path}")
        logger.warning("Static file serving will not be available")
        return
    
    # Add compression middleware for better performance
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add trusted host middleware for security
    if not settings.is_development():
        trusted_hosts = settings.get_trusted_hosts()
        if trusted_hosts and trusted_hosts != ["*"]:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
    
    # Mount static files with SPA support
    app.mount(
        "/static",
        StaticFiles(directory=frontend_path / "assets" if (frontend_path / "assets").exists() else frontend_path),
        name="static"
    )
    
    # Mount the main SPA static files handler
    # This should be mounted last to catch all remaining routes
    app.mount(
        "/",
        SPAStaticFiles(directory=frontend_path, html=True),
        name="spa"
    )
    
    logger.info(f"Static file serving configured for: {frontend_path}")

def add_static_file_headers(app: FastAPI) -> None:
    """
    Add middleware to set appropriate headers for static files.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.middleware("http")
    async def add_static_headers(request: Request, call_next):
        """Add caching and security headers for static files."""
        response = await call_next(request)
        
        # Add security headers for all responses
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Add caching headers for static assets
        if is_static_asset(request.url.path):
            # Cache static assets for a long time
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif request.url.path == "/" or request.url.path.endswith(".html"):
            # Don't cache HTML files to ensure SPA updates work
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

def create_fallback_index() -> str:
    """
    Create a fallback index.html if the frontend build is not available.
    
    Returns:
        HTML content for fallback page
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Agent Template</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                text-align: center;
                max-width: 600px;
                padding: 2rem;
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 1rem;
            }
            p {
                font-size: 1.2rem;
                margin-bottom: 2rem;
                line-height: 1.6;
            }
            .api-link {
                display: inline-block;
                background: rgba(255, 255, 255, 0.2);
                padding: 1rem 2rem;
                border-radius: 8px;
                text-decoration: none;
                color: white;
                font-weight: bold;
                transition: background 0.3s ease;
            }
            .api-link:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            .status {
                margin-top: 2rem;
                padding: 1rem;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Agent Template</h1>
            <p>
                The backend API is running successfully! 
                The frontend application is not yet available at this location.
            </p>
            <p>
                To build and serve the frontend, run:
                <br><code>cd frontend && npm run build</code>
            </p>
            <a href="/docs" class="api-link">📚 View API Documentation</a>
            <div class="status">
                <p><strong>✅ Backend Status:</strong> Running</p>
                <p><strong>📊 Health Check:</strong> <a href="/health" style="color: #90EE90;">/health</a></p>
                <p><strong>🤖 Agents:</strong> <a href="/agents" style="color: #90EE90;">/agents</a></p>
            </div>
        </div>
    </body>
    </html>
    """

def add_fallback_route(app: FastAPI) -> None:
    """
    Add a fallback route that serves a basic HTML page when frontend is not built.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/app", response_class=HTMLResponse)
    async def serve_fallback():
        """Serve fallback page when frontend is not available."""
        return create_fallback_index()

def setup_static_file_serving(app: FastAPI) -> None:
    """
    Main function to set up complete static file serving for the application.
    
    Args:
        app: FastAPI application instance
    """
    try:
        # Add static file headers middleware
        add_static_file_headers(app)
        
        # Configure static file serving
        configure_static_files(app)
        
        # Add fallback route
        add_fallback_route(app)
        
        logger.info("Static file serving setup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup static file serving: {e}")
        # Add fallback route even if static files fail
        add_fallback_route(app)

def get_static_file_info() -> dict:
    """
    Get information about static file serving configuration.
    
    Returns:
        Dictionary with static file configuration info
    """
    frontend_path = get_frontend_build_path()
    
    return {
        "frontend_build_path": str(frontend_path),
        "frontend_exists": frontend_path.exists(),
        "index_html_exists": (frontend_path / "index.html").exists(),
        "assets_directory": str(frontend_path / "assets") if (frontend_path / "assets").exists() else None,
        "static_file_serving": "enabled" if frontend_path.exists() else "disabled",
        "spa_routing": "enabled",
        "fallback_available": True
    } 