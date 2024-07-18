# THE GENERAL CONTAINER FOR CONNECTING ALL THE ENVIRONMENTS 😈
FROM ubuntu:22.04
FROM python:3.12.3-bullseye

#SYSTEM
ARG DEBIAN_FRONTEND=noninteractive
RUN usermod -s /bin/bash root
RUN apt-get update 

#RUST
RUN apt-get install curl nano build-essential cargo libstd-rust-dev -y

#JS 
RUN apt-get install -y nodejs npm
RUN npm install -g pm2 
ENV LIBNAME commune

WORKDIR /app
# WANT TO HAVE TO REBUILD THE WHOLE IMAGE EVERY TIME WE CHANGE THE REQUIREMENTS
COPY ./commune/requirements.txt /app/commune/requirements.txt
RUN pip install -r commune/requirements.txt
# THIS IS FOR THE LOCAL PACKAG
COPY ./ /app
RUN pip install -e ./ 
# IMPORT EVERYTHING ELSE
ENTRYPOINT [ "tail", "-f", "/dev/null"]