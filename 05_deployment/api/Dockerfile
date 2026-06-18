FROM python:3.13-slim

WORKDIR /work

COPY 05_deployment/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /work

EXPOSE 8050
CMD ["uvicorn", "app.main:app", "--app-dir", "/work/05_deployment/api", "--host", "0.0.0.0", "--port", "8050"]
