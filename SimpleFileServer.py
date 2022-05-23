import os
import time
import uuid

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse

import threading

data_dir = "/data/image.server"


def monitor_file_system(source_dir, keep_file_days):
    while True:
        print("Monitoring : " + source_dir)
        now = time.time() - keep_file_days * 86400
        for f in os.listdir(source_dir):
            fname = os.path.join(source_dir, f)
            if os.stat(fname).st_mtime < now:
                os.remove(fname)
        time.sleep(300)


app = FastAPI()


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
    t = threading.Thread(target=monitor_file_system, args=(data_dir, 15))

    t.start()
    uvicorn.run(app, port=8000, log_level="info")
