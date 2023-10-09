# Process multipart messages

Simple app processing multipart fields and files.
Fields are saved to memory, Files are saved to TemporaryFiles.
Solution is memory optimized.

## Getting Started

Clone project.

```
python3 scripts/generate_bigfile.py
```

Create and activate virtualenv. 

Run app
```
uvicorn multipart_upload.app:app
```

Run tests on another terminal (with the same virtualenv activated)
```
pytest
```

It is done like this so requests chunking can be exploited.
