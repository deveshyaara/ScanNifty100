"""Run python -m apps.etl.pipelines.refresh_all [--load] [--deploy]."""
import argparse
import logging
from apps.etl.pipelines.extract_n100 import extract
from apps.etl.pipelines.clean_transform import clean
from apps.analytics.pipeline import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", action="store_true")
    parser.add_argument("--deploy", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    extract()
    clean()
    run()
    if args.deploy or args.load:
        from apps.etl.load.warehouse import deploy, load
        if args.deploy:
            deploy()
        if args.load:
            logging.info("Warehouse published: %s", load())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
