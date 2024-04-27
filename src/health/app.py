import contextlib

import sqlalchemy as sa
from fastapi import FastAPI
from auth.adapter.api import router

__all__ = ["init_app"]

from health.config import Config
from health.logger import intercept_logs


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    db = app.config.db
    url = f"postgresql+pg8000://{db.username}:{db.password}@{db.host}:{db.port}/{db.database}"

    engine = sa.create_engine(url)
    setattr(app, "engine", engine)
    intercept_logs()

    yield

    engine.dispose(close=True)


def init_app(cfg: Config) -> FastAPI:
    app = FastAPI(
        docs_url=cfg.app.docs,
        lifespan=lifespan,
    )
    app.include_router(router)
    setattr(app, "config", cfg)

    return app
