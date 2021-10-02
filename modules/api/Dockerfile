FROM python:3.7-alpine

WORKDIR .

RUN apk add --no-cache gcc musl-dev linux-headers geos libc-dev postgresql-dev build-base
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 5000

COPY . .


RUN python -m grpc_tools.protoc -I./ --python_out=./ --grpc_python_out=./ location.proto


CMD ["flask", "run", "--host", "0.0.0.0"]
