"""
Script test upload/download file với MinIO qua thư viện minio-py.

Cài đặt trước khi chạy:
    pip install minio python-dotenv

Chạy:
    python scripts/upload_download.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()

ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "demo-bucket")

TEST_FILE_NAME = "test_upload.txt"
TEST_FILE_CONTENT = "Day la file test cho de tai MinIO distributed storage.\n"
DOWNLOAD_PATH = "downloaded_test_upload.txt"


def get_client() -> Minio:
    return Minio(
        ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False,  # True nếu dùng HTTPS
    )


def ensure_bucket(client: Minio, bucket_name: str) -> None:
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Đã tạo bucket: {bucket_name}")
    else:
        print(f"Bucket đã tồn tại: {bucket_name}")


def create_test_file() -> str:
    path = Path(TEST_FILE_NAME)
    path.write_text(TEST_FILE_CONTENT, encoding="utf-8")
    return str(path)


def upload_file(client: Minio, bucket_name: str, file_path: str) -> None:
    object_name = Path(file_path).name
    client.fput_object(bucket_name, object_name, file_path)
    print(f"Đã upload: {object_name}")


def download_file(client: Minio, bucket_name: str, object_name: str, download_path: str) -> None:
    client.fget_object(bucket_name, object_name, download_path)
    print(f"Đã download về: {download_path}")


def list_objects(client: Minio, bucket_name: str) -> None:
    print(f"\nDanh sách object trong bucket '{bucket_name}':")
    objects = client.list_objects(bucket_name)
    for obj in objects:
        print(f"  - {obj.object_name} ({obj.size} bytes)")


def main() -> None:
    client = get_client()

    try:
        ensure_bucket(client, BUCKET_NAME)

        file_path = create_test_file()
        upload_file(client, BUCKET_NAME, file_path)

        download_file(client, BUCKET_NAME, TEST_FILE_NAME, DOWNLOAD_PATH)

        list_objects(client, BUCKET_NAME)

        with open(DOWNLOAD_PATH, encoding="utf-8") as f:
            content = f.read()
        assert content == TEST_FILE_CONTENT, "Nội dung file tải về không khớp!"
        print("\nKiểm tra thành công: nội dung file upload và download khớp nhau.")

    except S3Error as err:
        print(f"Lỗi MinIO: {err}")


if __name__ == "__main__":
    main()
