FROM python:3

COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app
COPY app/ .

ENTRYPOINT [ "python", "app.py" ]