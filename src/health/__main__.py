import uvicorn
from .run import cfg

if __name__ == "__main__":
    uvicorn.run(
        app="health.run:app",
        reload=True,
        workers=cfg.app.workers,
        host=cfg.app.host,
        port=cfg.app.port,
        log_level=cfg.log.level,
    )
