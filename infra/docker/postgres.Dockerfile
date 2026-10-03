FROM postgres:15-alpine

COPY warehouse/ddl/ /docker-entrypoint-initdb.d/

ENV POSTGRES_DB=scannifty100
ENV POSTGRES_USER=scannifty100
ENV POSTGRES_PASSWORD=change-me
