from minio import Minio
from minio.error import S3Error
import os
import requests
import io

def run():
    # Create a client with the MinIO server playground, its access key
    # and secret key.
    client = Minio(
        "minio:9000",
        access_key=os.environ.get("MINIO_ROOT_USER"),
        secret_key=os.environ.get("MINIO_ROOT_PASSWORD"),
        secure=False,
    )

    bucket_name = os.environ.get("MINIO_DEFAULT_BUCKET")

    # Make 'my-bucket' bucket if not exist.
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
    else:
        print("Bucket 'my-bucket' already exists")

    result = client.put_object(
        bucket_name, "my-object", io.BytesIO(b"hello"), 5,
    )
    print(
        "created {0} object; etag: {1}, version-id: {2}".format(
            result.object_name, result.etag, result.version_id,
        ),
    )

    # Upload data from file.
    path = os.getcwd()
    files = os.listdir()
    print(path)
    print(files)


    result = client.fput_object(
        bucket_name, "0000", "/code/scripts_data/empty_art.png",
    )
    print(
        "created {0} object; etag: {1}, version-id: {2}".format(
            result.object_name, result.etag, result.version_id,
        ),
    )
