"""One-command local start:  python run.py"""
import uvicorn

from app.config import Settings
from app.main import create_app

if __name__ == "__main__":
    settings = Settings()
    if settings.generated_password:
        print(f"\n  Facilitator password (no FACILITATOR_PASSWORD set): {settings.facilitator_password}\n")
    if settings.development_mode:
        print("  DEVELOPMENT_MODE on: open /?dev_player=P1 .. P4 in four tabs (never enable in production).\n")
    print(f"  Open http://localhost:{settings.port}/facilitator   (players join at http://<this-machine-ip>:{settings.port}/)\n")
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
