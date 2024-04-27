from __future__ import annotations

import argparse
import functools

import yaml

from pathlib import Path
from typing import Literal, Sequence, TypeVar, Callable, ParamSpec

from pydantic_settings import BaseSettings
from pydantic import BaseModel, ValidationError, Field

__all__ = ["Config", "parse_yaml"]


class Config(BaseSettings):
    db: Database
    app: App
    log: Log


class Database(BaseModel):
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    sslmode: Literal["disable"]


class App(BaseModel):
    host: str = "localhost"
    port: int = 8080
    workers: int = 1
    docs: str = "/docs"
    secret: str


class Log(BaseModel):
    level: Literal["debug", "info", "warning", "error"] = "info"


class Args(BaseModel):
    config_path: Path = Field(default="config.yaml", alias="config")


Config.update_forward_refs()

ParamT = ParamSpec("ParamT")
RetT = TypeVar("RetT")


def catch_pydantic_errors(func: Callable[ParamT, RetT]) -> Callable[ParamT, RetT]:
    @functools.wraps(func)
    def wrapper(*args: ParamT.args, **kwargs: ParamT.kwargs) -> RetT:
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            from loguru import logger

            for error in e.errors():
                logger.error(f"Can't parse config: {error.get('msg')}")
            raise

    return wrapper


@catch_pydantic_errors
def parse_yaml(file_path: str | Path) -> Config:
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    with open(file_path, "r") as config_file:
        config_data = yaml.full_load(config_file)

    return Config.model_validate(obj=config_data)


@catch_pydantic_errors
def parse_args(args: Sequence[str]) -> Args:
    parser = argparse.ArgumentParser(
        prog="health",
        description="health server",
        add_help=True,
    )

    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Path to configuration file"
    )

    parsed_args = parser.parse_args(args)
    return Args.model_validate(
        parsed_args,
        strict=False,
        from_attributes=True,
    )
