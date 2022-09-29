#!/usr/bin/python


import os
import datetime
import glob
import io
import logging
import traceback
import sys
import pprint


data_dir = "/data/APGS/images"

LOC_LPR = 5

logger = logging.getLogger(__name__)

stored_data_dict = {}

def do_read_files():
    files = sorted(glob.glob(os.path.join(data_dir, "**/*.jpg"), recursive=True))
    for f in files:
        _list = f.split(".")

        if len(_list) != 11:
            logger.warning(f'invalid filename : {f}')
            continue
        key = _list[LOC_LPR]
        logger.info(f"key {key}")
        if key not in stored_data_dict:
            stored_data_dict[key] = []
        stored_data_dict[key].append(f)

    pprint.pprint(stored_data_dict)

def main():

    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.info("Test logg")
    do_read_files()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        sys.exit()
