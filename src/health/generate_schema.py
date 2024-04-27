import argparse
import json
import sys

from .config import Config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Config schema generator",
        "Generates json schema for config file",
    )

    parser.add_argument("-o", "--output", default="health-schema.json")
    args = parser.parse_args(sys.argv[1:])

    schema = Config.model_json_schema(by_alias=True)

    with open(args.output, "w") as output:
        json.dump(schema, output, indent=4)
