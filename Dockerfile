FROM python:3.8.10-slim-buster

RUN apt-get update

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY CFSUtils.py /apps/CFSUtils.py
COPY SimpleFileServer.py /apps/SimpleFileServer.py
COPY run.sh /apps/run.sh
COPY version.py /apps/version.py

CMD ["/apps/run.sh"]
