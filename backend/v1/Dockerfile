FROM ait/taggerxvfb

WORKDIR /app
COPY src/ ./
COPY entrypoint.sh ./

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]