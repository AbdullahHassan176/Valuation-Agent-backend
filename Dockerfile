FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn[standard] pydantic httpx
COPY . .
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
