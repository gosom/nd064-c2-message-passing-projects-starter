FROM python:3.7-alpine
RUN apk add --no-cache gcc musl-dev linux-headers geos libc-dev postgresql-dev build-base


WORKDIR .

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .
RUN python -m grpc_tools.protoc -I./app --python_out=./app --grpc_python_out=./app location.proto

EXPOSE 5005

CMD ["python", "app/main.py"]
