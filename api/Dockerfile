# server setup
FROM python:3.9

COPY . api

WORKDIR api

RUN chmod +x requirements.txt

RUN pip install -r requirements.txt --no-cache-dir --compile

ENV FLASK_ENV="production"

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/api
EXPOSE 5000

CMD ["flask", "run", "--host","0.0.0.0"]