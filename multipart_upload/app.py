from typing import Optional

from fastapi import FastAPI, Request

from .multipart import create_boundary_and_content_type, create_parser

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


from time import sleep


@app.post("/multipart_upload/")
async def multipart_upload(request: Request):
    # TO-DO sanitize headers

    content_type, boundary = create_boundary_and_content_type(request.headers)

    if not boundary:
        return {"ERROR": "No multipart boundary"}

    parsed_fields, parsed_files = [], []

    parser = create_parser(boundary, parsed_fields, parsed_files)

    i = 0
    async for chunk in request.stream():
        print(i := i + 1)
        parser.write(chunk)

    # At this point fields and files are ready for further processing.
    for file in parsed_files:
        print("File: ", file)
        file.close()
        sleep(5)

    for field in parsed_fields:
        print("Field: ", field)

    return {"Hello": "World"}
