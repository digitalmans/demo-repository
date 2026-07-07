FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud platforms automatically provide $PORT
EXPOSE 8765

CMD ["python", "interactive_server.py"]
