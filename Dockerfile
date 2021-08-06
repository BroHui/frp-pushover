FROM python:3.8-slim as base
WORKDIR /wheels
COPY ./requirements.txt .
RUN apt-get update && \
    apt-get install -y \
	default-libmysqlclient-dev \
	libmariadb3 \
	gcc
RUN pip install -U pip \
	&& pip install --no-cache-dir wheel \
	&& pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.8-slim
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app
COPY --from=base /wheels /wheels
COPY --from=base /usr/lib/x86_64-linux-gnu/libmariadb.so.3 /usr/lib/x86_64-linux-gnu/
RUN pip install -U pip \
	&& pip install -f /wheels -r /wheels/requirements.txt \
	&& rm -rf /wheels \
	&& rm -rf /root/.cache/pip/*
ENV TZ=Asia/Hong_Kong
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . /usr/src/app
EXPOSE 8080 8081
CMD ["uwsgi", "--ini", "uwsgi.ini"]
