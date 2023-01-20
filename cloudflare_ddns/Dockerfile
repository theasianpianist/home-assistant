ARG BUILD_FROM
FROM $BUILD_FROM

RUN \
    apk add --no-cache \
        python3

COPY run.py /
RUN chmod a+x /run.py

CMD [ "/run.py" ]
