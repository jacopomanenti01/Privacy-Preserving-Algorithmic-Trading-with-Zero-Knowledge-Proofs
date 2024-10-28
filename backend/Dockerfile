FROM python:3.9

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /usr/app/src
COPY hello_world.py ./