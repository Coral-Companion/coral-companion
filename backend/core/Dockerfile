FROM python:3.11-slim

# explicitly install no-cuda torch and torchvision
RUN pip install --no-cache-dir \
    torch==2.5.0 \
    torchvision==0.20.0 \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]