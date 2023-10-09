import os

FILE_PATH = "./test/multipart_nested_bigfile"

BOUNDARY = "===============outer123456=="

BINARY_DATA_START = "SomePicture binary data ..... "

MULTIPART_FORM = f'--{BOUNDARY}\r\nContent-Type: application/xml\r\nContent-Disposition: form-data; name="root-fields"\r\n\r\n\r\n<?xml version="1.0" encoding="UTF-8"?>\r\n<nms:object xmlns:nms="urn:oma:xml:rest:netapi:nms:1">\r\n<parentFolder>http://example.com/exampleAPI/nms/v1/myStore/tel%3A%2B19585550100/folders/fld123</parentFolder>\r\n\r\n<attributes/>\r\n<flags>\r\n<flag>\Seen</flag>\r\n<flag>\Flagged</flag>\r\n</flags>\r\n</nms:object>\r\n--{BOUNDARY}\r\nContent-Type: multipart/mixed; boundary="--=-sep-=--"\r\nContent-Disposition: form-data; name="attachments"\r\n\r\n\r\n----=-sep-=--\r\nContent-Type: text/plain\r\nContent-Disposition: attachment; filename="body.txt"\r\n\r\nSee attached photo\r\n----=-sep-=--\r\nContent-Type: image/gif\r\nContent-Disposition: attachment; filename="picture.gif"\r\n\r\n{BINARY_DATA_START}\r\n--{BOUNDARY}--\r\n'


def encode_line(line: str) -> bytes:
    return bytes(line, encoding="utf-8")


def generate_2GB():
    MAX_SIZE = 2000000000
    CHUNK_SIZE = 1024
    current_size = 0

    while current_size < MAX_SIZE:
        yield os.urandom(CHUNK_SIZE)
        current_size += CHUNK_SIZE


def generate_bigfile():
    with open(FILE_PATH, "wb") as fp:
        for line in MULTIPART_FORM.split("\n"):
            if BINARY_DATA_START in line:
                for random_bytes in generate_2GB():
                    fp.write(random_bytes)

            fp.write(encode_line(f"{line}\n"))


if __name__ == "__main__":
    generate_bigfile()
