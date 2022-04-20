FROM ubuntu

RUN apt-get update
RUN apt-get install ca-certificates -y
RUN apt-get install python3 python3-pip python3-venv git libpq-dev -y

WORKDIR /ethereum-etl

RUN git clone -b phillip/load-parquet https://github.com/spicehq/ethereum-etl.git .

WORKDIR /ethereum-etl
RUN python3 -m venv venv
RUN venv/bin/pip3 install -r requirements.txt
RUN venv/bin/python3 /ethereum-etl/ethereumetl.py --version
