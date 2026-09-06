FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
ENV FLASK_ENV=production
EXPOSE 5000

CMD ["sh", "-c", "gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:${PORT} app:app"]
