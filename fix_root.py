import os

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import for RedirectResponse at top
content = content.replace(
    'from fastapi.staticfiles import StaticFiles',
    'from fastapi.staticfiles import StaticFiles\nfrom fastapi.responses import RedirectResponse'
)

# Add root route before include_router
old = '''    # Serve static frontend
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(router, prefix=settings.API_PREFIX)'''

new = '''    # Serve static frontend
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def root():
        """Redirect root to frontend."""
        return RedirectResponse(url="/static/index.html")

    app.include_router(router, prefix=settings.API_PREFIX)'''

content = content.replace(old, new)

with open('app/main.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print('main.py fixed')
