FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y supervisor

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt supervisor

COPY . .

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]