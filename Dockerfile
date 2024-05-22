FROM python:3.11

WORKDIR /app

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


EXPOSE 5500

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8080","--reload"]