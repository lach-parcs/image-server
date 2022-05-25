import logging
import os
import time
import uuid

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi_utils.tasks import repeat_every

logger = logging.getLogger(__name__)
data_dir = "/data/image.server"
temp_dir = data_dir + "/temp"

if not os.path.isdir(temp_dir):
    os.makedirs(temp_dir)

keep_file_days = 15

app = FastAPI()


@app.on_event("startup")
@repeat_every(seconds=1800, logger=logger, wait_first=False)
def periodic_cleaner():
    now = time.time() - keep_file_days * 86400
    for f in os.listdir(data_dir):
        fname = os.path.join(data_dir, f)
        if os.stat(fname).st_mtime < now:
            os.remove(fname)


@app.post("/v1/image-temp")
async def upload_file(file: UploadFile = File(...)):
    save_file_name = os.path.basename(file.filename)
    data_name = os.path.join(temp_dir, save_file_name)
    with open(data_name, 'wb') as image:
        content = await file.read()
        image.write(content)
        image.close()
    return JSONResponse(content={"uuid": save_file_name}, status_code=200)


@app.post("/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    save_file_name = str(uuid.uuid1()) + ".jpg"
    data_name = os.path.join(data_dir, save_file_name)
    with open(data_name, 'wb') as image:
        content = await file.read()
        image.write(content)
        image.close()
    return JSONResponse(content={"uuid": save_file_name}, status_code=200)


@app.get("/v1/download/{name_file}")
def download_file(name_file: str):
    return FileResponse(path=os.path.join(data_dir, name_file), media_type='application/octet-stream', filename=name_file)


if __name__ == "__main__":
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
