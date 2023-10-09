from multipart_upload.multipart import Field, File


def test_field_write():
    def local_read(f):
        return f._data

    expected = bytes("abcbncbcbcb", encoding="utf-8")

    f = Field({})

    f.write(expected)

    assert local_read(f) == expected


def test_field_read():
    def local_write(f, data):
        f._data = data

    expected = bytes("abcbncbcbcb", encoding="utf-8")

    f = Field({})

    local_write(f, expected)

    assert f.read() == expected


def test_field_read_in_chunks():
    def local_write(f, data):
        f._data = data

    def local_decode(bytes_):
        return bytes_.decode()

    expected = bytes("abcbncbcbcb", encoding="utf-8")

    f = Field({})
    local_write(f, expected)

    i = 0
    while chunk := f.read_chunk(1):
        assert local_decode(chunk) == local_decode(expected)[i]
        i += 1


def test_file_write():
    def local_read(f):
        return f._tempfile.read()

    expected = [
        bytes("abcbncbcbcb", encoding="utf-8"),
        bytes("Jestem", encoding="utf-8"),
        bytes("Kotki", encoding="utf-8"),
    ]

    f = File({})

    for exp in expected:
        f.write(exp)

    assert local_read(f) == b"".join(expected)


def test_file_read_in_chunks():
    def local_write(f, data):
        f._data = data

    def local_decode(bytes_):
        return bytes_.decode()

    expected = [
        bytes("abcbncbcbcb", encoding="utf-8"),
        bytes("Jestem", encoding="utf-8"),
        bytes("Kotki", encoding="utf-8"),
    ]

    f = Field({})

    for exp in expected:
        local_write(f, exp)

        i = 0
        while chunk := f.read_chunk(1):
            assert local_decode(chunk) == local_decode(b"".join(expected))[i]
            i += 1
