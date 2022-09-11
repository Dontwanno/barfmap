FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine
RUN apk --update add bash nano
ENV FLASK_APP flaskr
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt