#
# APGS-ImageServer
#
# Created at 22. 11. 22.
# Copyrights (C) 2021 doroami@HumaxParcs all rights reserved
#
import datetime
import glob
import os
import bisect
import shutil

FNAME_INDEX_VALID_NUM = 11
FNAME_INDEX_MS_IN_DAY = 0
FNAME_INDEX_DATETIME = 1
FNAME_INDEX_REGION_ID = 2
FNAME_INDEX_CAM_TYPE = 3
FNAME_INDEX_CAM_ID = 4
FNAME_INDEX_CAM_VALUE = 5
FNAME_INDEX_CAM_VALUE_POS_X = 6
FNAME_INDEX_CAM_VALUE_POS_Y = 7
FNAME_INDEX_CAM_VALUE_WIDTH = 8
FNAME_INDEX_CAM_VALUE_HEIGHT = 9


class CFSUtils:
    @staticmethod
    def read_images(data_dir, keep_day):
        found_dicts = {}
        for f in glob.glob(os.path.join(data_dir, "**/*.jpg"), recursive=True):
            fname = os.path.basename(f)
            car_id = CFSUtils.is_valid_lpr_name(fname)
            if car_id:
                if car_id not in found_dicts:
                    found_dicts[car_id] = []

                bisect.insort(found_dicts[car_id], os.path.join(os.path.basename(os.path.dirname(f)), fname))

        current = datetime.datetime.now() - datetime.timedelta(days=keep_day)
        for k in found_dicts.keys():
            nl = [f for f in found_dicts[k] if not CFSUtils.is_outdated_file(f, current)]
            if nl:
                found_dicts[k] = nl
            else:
                fn = found_dicts[k][-1]
                if not fn.startswith("outdated"):
                    shutil.move(os.path.join(data_dir, fn), os.path.join(os.path.join(data_dir, "outdated"), os.path.basename(fn)))
                # OutDated인 경우, 따로 보관 폴더로 이동하자
                found_dicts[k] = [os.path.join("outdated", os.path.basename(fn))]

        for d in os.listdir(data_dir):
            try:
                d_time = datetime.datetime.strptime(d, "%Y%m%d")
                if d_time < current:
                    shutil.rmtree(os.path.join(data_dir, d))

            except ValueError:
                continue

        return found_dicts

    @staticmethod
    def is_valid_lpr_name(fname):
        f_items = fname.split(".")

        if len(f_items) == FNAME_INDEX_VALID_NUM:
            return f_items[FNAME_INDEX_CAM_VALUE]

        return ""

    @staticmethod
    def is_outdated_file(fname, outdated_from):
        d = fname.split(".")[FNAME_INDEX_DATETIME]
        current = datetime.datetime.strptime(d, "%Y%m%d%H%M%S")
        return current <= outdated_from

