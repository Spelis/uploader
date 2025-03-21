FROM python:3.13.2
WORKDIR /opt/uploader
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host 0.0.0.0", "--port 80"]
