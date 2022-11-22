import datetime
import io
import logging
import os

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi_utils.tasks import repeat_every
from starlette.responses import StreamingResponse

from CFSUtils import CFSUtils, FNAME_INDEX_CAM_VALUE, FNAME_INDEX_CAM_VALUE_HEIGHT, FNAME_INDEX_CAM_VALUE_WIDTH, FNAME_INDEX_CAM_VALUE_POS_Y, FNAME_INDEX_CAM_VALUE_POS_X
from version import VERSION

"""
    하루 한번 데이타 신규 정리
    차량별 한개의 이미지 이상은 항상 유지
    특정 API를 통해서 해당 번호 삭제 필요
    차량별 번호 폴더는 별도 정의 --> 형식 정해져 있음
"""

Logger = logging.getLogger(__name__)
DATA_DIR = "/data/APGS/images"
KEEP_IMAGE_DAYS = 15

app = FastAPI()

saved_data_list = {}


@app.on_event("startup")
def initialize():
    global saved_data_list

    Logger.info("initialize all data")
    saved_data_list = CFSUtils.read_images(DATA_DIR, KEEP_IMAGE_DAYS)


@repeat_every(seconds=3600, logger=Logger, wait_first=False)
def refine_saved_images():
    global saved_data_list

    Logger.info("Refine ALL saved images")
    saved_data_list = CFSUtils.read_images(DATA_DIR, KEEP_IMAGE_DAYS)


@app.get("/")
async def get_version():
    return JSONResponse(content={"version": VERSION}, status_code=200)


@app.post("/v1/upload")
@app.post("/v1/image-temp")
async def upload_file_temp(file: UploadFile = File(...)):
    global saved_data_list

    save_file_name = os.path.basename(file.filename)
    now = datetime.datetime.now()
    dirname = os.path.join(DATA_DIR, now.strftime("%Y%m%d"))
    data_name = os.path.join(dirname, now.strftime("%H%M%S%f")[:-3] + "." + save_file_name)

    _tlist = save_file_name.split(".")
    if len(_tlist) != 10:
        Logger.warning(f"invalid filename format :{save_file_name} ")
        return JSONResponse(content={"uuid": save_file_name, "result": "nok"}, status_code=404)

    key = _tlist[FNAME_INDEX_CAM_VALUE - 1]
    if key not in saved_data_list:
        saved_data_list[key] = []
    saved_data_list[key].append(data_name)

    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    with open(data_name, 'wb') as image:
        content = await file.read()
        image.write(content)
        image.close()
    return JSONResponse(content={"uuid": save_file_name, "result": "ok"}, status_code=200)


@app.get("/v1/download/latest")
async def download_latest(lpr: str):
    global saved_data_list
    if lpr in saved_data_list:
        data_name = saved_data_list[lpr][-1]
        return StreamingResponse(io.BytesIO(open(os.path.join(DATA_DIR, data_name), "rb").read()), media_type="image/jpg")

    return JSONResponse(content={"result": "nok"}, status_code=404)


@app.get("/v1/download/latest2")
async def download_latest2(lpr: str):
    global saved_data_list

    if lpr in saved_data_list:
        data_name = saved_data_list[lpr][-1]
        return StreamingResponse(io.BytesIO(open(os.path.join(DATA_DIR, data_name), "rb").read()), media_type="image/jpg")

    return JSONResponse(content={"result": "nok"}, status_code=404)


@app.get("/v1/download/latesturl2")
async def download_latesturli2(lpr: str):
    global saved_data_list

    if lpr in saved_data_list:
        data_name = saved_data_list[lpr][-1]
        Logger.info(f"data_name {data_name}")
        _datums = data_name.split(".")
        Logger.info(f"{_datums}")
        if len(_datums) < (FNAME_INDEX_CAM_VALUE_HEIGHT + 2):
            _lp_startx = 0
            _lp_starty = 0
            _lp_width = 0
            _lp_height = 0
        else:
            _lp_startx = _datums[FNAME_INDEX_CAM_VALUE_POS_X]
            _lp_starty = _datums[FNAME_INDEX_CAM_VALUE_POS_Y]
            _lp_width = _datums[FNAME_INDEX_CAM_VALUE_WIDTH]
            _lp_height = _datums[FNAME_INDEX_CAM_VALUE_HEIGHT]

        # return JSONResponse(content={"url": "/v1/download/latest?lpr=" + lpr, "result": "ok"}, status_code=200)
        return JSONResponse(content={"url": "/v1/download/latest?lpr=" + lpr, "plate_startx": _lp_startx, "plate_starty": _lp_starty, "plate_width": _lp_width, "plate_height": _lp_height, "result": "ok"},
                            status_code=200)
        # return FileResponse(path=data_name, media_type="image/jpeg", filename=os.path.basename(data_name))
    return JSONResponse(content={"result": "nok"}, status_code=404)


@app.get("/v1/download/latesturl")
async def download_latesturl(lpr: str):
    global saved_data_list

    if lpr in saved_data_list:
        data_name = saved_data_list[lpr][-1]
        return JSONResponse(content={"url": "/v1/download/latest?lpr=" + lpr, "result": "ok"}, status_code=200)
        # return FileResponse(path=data_name, media_type="image/jpeg", filename=os.path.basename(data_name))
    return JSONResponse(content={"result": "nok"}, status_code=404)


@app.get("/v1/search")
async def search(lpr: str):
    global saved_data_list

    found_list = []
    start = len(DATA_DIR)
    for _, data in saved_data_list.items():
        if lpr in _:
            found_list += [d[start + 1:] for d in data]

    return JSONResponse(content=found_list, status_code=200)


@app.get("/v1/download")
async def download_specific(path_name: str):
    full_name = os.path.join(DATA_DIR, path_name)
    if os.path.isfile(full_name):
        return StreamingResponse(io.BytesIO(open(full_name, "rb").read()), media_type="image/jpg")

    return JSONResponse(content={"result": "nok"}, status_code=404)


if __name__ == "__main__":
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.isdir(os.path.join(DATA_DIR, "outdated")):
        os.makedirs(os.path.join(DATA_DIR, "outdated"))

    Logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    Logger.addHandler(stream_handler)

    Logger.info("Test logg")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
