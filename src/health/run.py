import sys

from health.logger import prepare_logger
from . import config
from .app import init_app

args = config.parse_args(sys.argv[1:])
cfg = config.parse_yaml(args.config_path)

app = init_app(cfg)
prepare_logger(cfg.log.level.upper())
