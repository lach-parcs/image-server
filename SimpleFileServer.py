import datetime
import glob
import io
import logging
import os
import shutil

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi_utils.tasks import repeat_every
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)
data_dir = "/data/APGS/images"

keep_file_days = 15

app = FastAPI()

stored_data_dict = {}


@app.on_event("startup")
def read_all_file_tree():
    files = glob.glob(os.path.join(data_dir, "**/*.jpg"), recursive=True)
    for f in files:
        key = f.split(".")[-2]
        if key not in stored_data_dict:
            stored_data_dict[key] = []
        stored_data_dict[key].append(f)


@repeat_every(seconds=3600, logger=logger, wait_first=False)
def periodic_cleaner():
    dir_list = sorted(os.listdir(data_dir))
    dir_list = dir_list[: -keep_file_days]
    for d in dir_list:
        shutil.rmtree(os.path.join(data_dir, d))


@app.post("/v1/upload")
@app.post("/v1/image-temp")
async def upload_file_temp(file: UploadFile = File(...)):
    save_file_name = os.path.basename(file.filename)
    now = datetime.datetime.now()
    dirname = os.path.join(data_dir, now.strftime("%Y%m%d"))
    data_name = os.path.join(dirname, now.strftime("%H%M%S%f")[:-3] + "." + save_file_name)

    key = save_file_name.split(".")[-2]
    if key not in stored_data_dict:
        stored_data_dict[key] = []
    stored_data_dict[key].append(data_name)

    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    with open(data_name, 'wb') as image:
        content = await file.read()
        image.write(content)
        image.close()
    return JSONResponse(content={"uuid": save_file_name, "result": "ok"}, status_code=200)


@app.get("/v1/download/latest")
async def download_latest(lpr: str):
    if lpr in stored_data_dict:
        data_name = stored_data_dict[lpr][-1]
        return StreamingResponse(io.BytesIO(open(data_name, "rb").read()), media_type="image/jpg")
        # return FileResponse(path=data_name, media_type="image/jpeg", filename=os.path.basename(data_name))
    return JSONResponse(content={"result": "nok"}, status_code=404)


@app.get("/v1/download/latesturl")
async def download_latesturl(lpr: str):
    if lpr in stored_data_dict:
        data_name = stored_data_dict[lpr][-1]

        return JSONResponse(content={"url": data_name.replace(data_dir + "/", ""), "result": "ok"}, status_code=200)
        # return FileResponse(path=data_name, media_type="image/jpeg", filename=os.path.basename(data_name))
    return JSONResponse(content={"result": "nok"}, status_code=404)


@app.get("/v1/search")
async def search(lpr: str):
    found_list = []
    start = len(data_dir)
    for _, data in stored_data_dict.items():
        if lpr in _:
            found_list += [d[start + 1:] for d in data]

    return JSONResponse(content=found_list, status_code=200)


@app.get("/v1/download")
async def download_specific(path_name: str):
    full_name = os.path.join(data_dir, path_name)
    if os.path.isfile(full_name):
        return StreamingResponse(io.BytesIO(open(full_name, "rb").read()), media_type="image/jpg")

    return JSONResponse(content={"result": "nok"}, status_code=404)

# @app.post("/v1/upload")
# async def upload_file(file: UploadFile = File(...)):
#     save_file_name = str(uuid.uuid1()) + ".jpg"
#     data_name = os.path.join(data_dir, save_file_name)
#     with open(data_name, 'wb') as image:
#         content = await file.read()
#         image.write(content)
#         image.close()
#     return JSONResponse(content={"uuid": save_file_name}, status_code=200)
#
#
# @app.get("/v1/download/{name_file}")
# def download_file(name_file: str):
#     return FileResponse(path=os.path.join(data_dir, name_file), media_type='application/octet-stream', filename=name_file)


if __name__ == "__main__":

    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
