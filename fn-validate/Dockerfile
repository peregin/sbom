FROM ghcr.io/fnproject/python:3.11-dev as build-stage

WORKDIR /function

COPY requirements.txt .
RUN pip install --target /python/ --no-cache-dir -r requirements.txt

COPY func.py func.yaml ./
COPY schemas ./schemas

FROM ghcr.io/fnproject/python:3.11
WORKDIR /function

COPY --from=build-stage /python /python
COPY func.py func.yaml ./
COPY schemas ./schemas

CMD ["/python/bin/fdk", "/function/func.py", "handler"]
