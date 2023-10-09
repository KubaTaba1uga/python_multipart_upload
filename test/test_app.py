import asyncio
from time import sleep
from unittest.mock import MagicMock

import pytest
import requests
from aiohttp import MultipartReader
from aiohttp.base_protocol import BaseProtocol
from aiohttp.hdrs import CONTENT_TYPE
from fastapi.testclient import TestClient

from multipart_upload.app import app, create_boundary_and_content_type
from multipart_upload.multipart import create_parser

BOUNDARY = "===============outer123456=="

REQUEST_BODY = f'--{BOUNDARY}\r\nContent-Type: application/xml\r\nContent-Disposition: form-data; name="root-fields"\r\n\r\n<?xml version="1.0" encoding="UTF-8"?>\r\n<nms:objectList xmlns:nms="urn:oma:xml:rest:netapi:nms:1">\r\n</nms:objectList>\r\n--{BOUNDARY}\r\nContent-Disposition: form-data; name="attachments"\r\nContent-Type: application/json\r\n\r\nA\r\n--{BOUNDARY}\r\nContent-Disposition: form-data; name="attachments"\r\nContent-Type: application/json\r\n\r\nB\r\n--{BOUNDARY}--\r\n'

REQUEST_NESTED_BODY = f'--{BOUNDARY}\r\nContent-Type: application/xml\r\nContent-Disposition: form-data; name="root-fields"\r\n\r\n<?xml version="1.0" encoding="UTF-8"?>\r\n<nms:objectList xmlns:nms="urn:oma:xml:rest:netapi:nms:1">\r\n</nms:objectList>\r\n--{BOUNDARY}\r\nContent-Type: multipart/mixed; boundary="--=-sep-=--"\r\nContent-Disposition: form-data; name="attachments"\r\n\r\n----=-sep-=--\r\nContent-Disposition: form-data; name="attachments"\r\nContent-Type: application/json\r\n\r\nA\r\n----=-sep-=--\r\nContent-Disposition: form-data; name="attachments"\r\nContent-Type: application/json\r\n\r\nB\r\n--{BOUNDARY}--\r\n'

REQUEST_HEADERS = {CONTENT_TYPE: f'multipart/form-data; boundary="{BOUNDARY}"'}

BODY_IN_CHUNKS = [
    bytes(f"{chunk}\n", encoding="utf-8") for chunk in REQUEST_BODY.split("\n")
]
EXPECTED = [
    bytearray(
        b'<?xml version="1.0" encoding="UTF-8"?>\r\n<nms:objectList xmlns:nms="urn:oma:xml:rest:netapi:nms:1">\r\n</nms:objectList>'
    ),
    bytearray(b"A"),
    bytearray(b"B"),
]


def encode_line(line: str) -> bytes:
    return bytes(f"{line}\n", encoding="utf-8")


def generate_file_chunks():
    with open("test/multipart_nested_file", "rb") as fp:
        while chunk := fp.read(100):
            yield chunk
            # thanks to sleeping server won't buffor small chunks into bigger ones
            sleep(0.000000000000000000000000000000001)


def generate_bigfile_chunks():
    with open("test/multipart_nested_bigfile", "rb") as fp:
        while chunk := fp.read(10240):
            yield chunk


def generate_chunks():
    for line in REQUEST_BODY.split("\n"):
        yield encode_line(line)
        sleep(0.000000000000000000000001)


def generate_nested_chunks():
    for line in REQUEST_NESTED_BODY.split("\n"):
        yield encode_line(line)
        sleep(0.000000000000000000000001)


url = "http://127.0.0.1:8000/multipart_upload/"


def test_create_boundary_and_content_type():
    content_type, boundary = create_boundary_and_content_type(REQUEST_HEADERS)

    assert content_type == "multipart/form-data"
    assert boundary == f"{BOUNDARY}"


def test_working_simple():
    response = requests.post(
        url, headers=REQUEST_HEADERS, data=generate_chunks(), stream=True
    )
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_working_advanced():
    response = requests.post(
        url, headers=REQUEST_HEADERS, data=generate_file_chunks(), stream=True
    )
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


# @pytest.mark.skip(reason="this test takes too much time, one can run it explicitly")
def test_working_bigfile():
    response = requests.post(
        url, headers=REQUEST_HEADERS, data=generate_bigfile_chunks(), stream=True
    )
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


from unittest.mock import patch

client = TestClient(app)


def test_working_simple_fields_creation():
    expected = [
        {
            "headers": {
                "Content-Type": "application/xml",
                "Content-Disposition": 'form-data; name="root-fields"',
            },
            "content": b'<?xml version="1.0" encoding="UTF-8"?>\r\n<nms:objectList xmlns:nms="urn:oma:xml:rest:netapi:nms:1">\r\n</nms:objectList>',
        },
        {
            "headers": {
                "Content-Disposition": 'form-data; name="attachments"',
                "Content-Type": "application/json",
            },
            "content": b"A",
        },
        {
            "headers": {
                "Content-Disposition": 'form-data; name="attachments"',
                "Content-Type": "application/json",
            },
            "content": b"B",
        },
    ]

    content_type, boundary = create_boundary_and_content_type(REQUEST_HEADERS)
    parsed_fields, parsed_files = [], []

    parser = create_parser(boundary, parsed_fields, parsed_files)

    for chunk in generate_chunks():
        parser.write(chunk)

    for i, exp in enumerate(expected):
        assert parsed_fields[i].headers == exp["headers"]
        assert parsed_fields[i]._data == exp["content"]


def test_working_nested_fields_creation():
    expected = [
        {
            "headers": {
                "Content-Type": "application/xml",
                "Content-Disposition": 'form-data; name="root-fields"',
            },
            "content": b'<?xml version="1.0" encoding="UTF-8"?>\r\n<nms:objectList xmlns:nms="urn:oma:xml:rest:netapi:nms:1">\r\n</nms:objectList>',
        },
        {
            "headers": {
                "Content-Disposition": 'form-data; name="attachments"',
                "Content-Type": "application/json",
            },
            "content": b"A",
        },
        {
            "headers": {
                "Content-Disposition": 'form-data; name="attachments"',
                "Content-Type": "application/json",
            },
            "content": b"B",
        },
    ]

    content_type, boundary = create_boundary_and_content_type(REQUEST_HEADERS)
    parsed_fields, parsed_files = [], []

    parser = create_parser(boundary, parsed_fields, parsed_files)

    for chunk in generate_nested_chunks():
        parser.write(chunk)

    for i, exp in enumerate(expected):
        assert parsed_fields[i].headers == exp["headers"]
        assert parsed_fields[i]._data == exp["content"]
