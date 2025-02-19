FROM python:3.9

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=api/v1/app.python
ENV FLASK-ENV=development

CMD ["flask", "run", "--host=0.0.0.0"]