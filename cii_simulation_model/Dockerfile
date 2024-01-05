FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip

COPY . /app/
COPY requirements.txt /app/

RUN pip3 install --no-cache-dir --default-timeout=1000 -r requirements.txt

EXPOSE 80

CMD ["python3", "/app/app.py"]
