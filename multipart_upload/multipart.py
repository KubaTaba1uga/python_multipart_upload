from abc import ABC
from tempfile import TemporaryFile

from multipart.multipart import MultipartParser, parse_options_header


class FieldAbs(ABC):
    def __init__(self, headers: dict):
        self.headers = headers

    def read_chunk(self, chunk_size: int) -> bytes:
        raise NotImplementedError()

    def read(self) -> bytes:
        raise NotImplementedError()

    def write(self, data: bytes) -> None:
        raise NotImplementedError()


class Field(FieldAbs):
    CONTENT_TYPES = {"application/xml": True, "application/json": True}

    def __init__(self, headers: dict):
        self._data = b""
        self._i = 0

        super().__init__(headers)

    def read_chunk(self, chunk_size: int) -> bytes:
        old_lenth, new_length = self._i, self._i + chunk_size

        data = self._data[old_lenth:new_length]

        self._i = new_length

        return data

    def read(self) -> bytes:
        return self._data

    def write(self, data: bytes):
        self._data += data


import io


class File(FieldAbs):
    MAX_BUFFER_SIZE = 1024 * 10
    CONTENT_TYPES = {"text/plain": True, "image/gif": True}

    def __init__(self, headers: dict):
        self._tempfile = TemporaryFile(mode="w+b", buffering=self.MAX_BUFFER_SIZE)

        super().__init__(headers)

    def read_chunk(self, chunk_size: int) -> bytes:
        return self._tempfile.read(chunk_size)

    def read(self):
        return self._tempfile.read()

    def write(self, data: bytes):
        """Writes to the file's end."""
        current_i = self._tempfile.tell()
        self._tempfile.seek(0, io.SEEK_END)

        self._tempfile.write(data)

        self._tempfile.seek(current_i)

    def close(self):
        self._tempfile.close()


def create_boundary_and_content_type(headers: dict) -> tuple:
    CONTENT_TYPE_VARIANTS = ["Content-Type", "content-type"]

    for type_ in CONTENT_TYPE_VARIANTS:
        if content_type_hdr := headers.get(type_):
            break

    if not content_type_hdr:
        return None, None

    content_type_hdr = bytes(content_type_hdr, encoding="utf-8")

    parsed_header = parse_options_header(content_type_hdr)

    if not parsed_header:
        return None, None

    content_type, params = parsed_header

    boundary = params.get(b"boundary")

    return content_type.decode(), boundary.decode() if boundary else None


def create_parser(boundary: str, fields: list, files: list):
    tmp_values = {}
    headers = {}

    def _create_tmp_header():
        tmp_values["header_name"] = b""
        tmp_values["header_value"] = b""

    def on_part_begin():
        _create_tmp_header()

    def on_header_begin():
        pass

    def on_header_field(data, start, end):
        tmp_values["header_name"] += data[start:end]

    def on_header_value(data, start, end):
        tmp_values["header_value"] += data[start:end]

    def on_header_end():
        # write header
        headers[tmp_values["header_name"].decode()] = tmp_values[
            "header_value"
        ].decode()

        # clean tmp values
        _create_tmp_header()

    def on_headers_finished():
        del tmp_values["header_name"]
        del tmp_values["header_value"]

        meta = create_boundary_and_content_type(headers)

        if not meta:
            return

        content_type, boundary = meta

        if boundary and "multipart" in content_type:
            tmp_values["field_handler"] = create_parser(boundary, fields, files)
        elif File.CONTENT_TYPES.get(content_type):
            tmp_values["field_handler"] = File(headers.copy())
            files.append(tmp_values["field_handler"])
        elif Field.CONTENT_TYPES.get(content_type):
            tmp_values["field_handler"] = Field(headers.copy())
            fields.append(tmp_values["field_handler"])
        else:
            raise NotImplementedError()

    def on_part_data(data, start, end):
        tmp_values["field_handler"].write(data[start:end])

    def on_part_end():
        tmp_values.clear()
        headers.clear()

    def on_end():
        print("MULTIPART FORM PROCESSED")

    return MultipartParser(
        boundary=boundary,
        callbacks={
            "on_part_begin": on_part_begin,
            "on_part_data": on_part_data,
            "on_part_end": on_part_end,
            "on_header_begin": on_header_begin,
            "on_header_field": on_header_field,
            "on_header_value": on_header_value,
            "on_header_end": on_header_end,
            "on_headers_finished": on_headers_finished,
            "on_end": on_end,
        },
    )
