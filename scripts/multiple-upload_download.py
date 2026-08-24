"""
MinIO Multiple File Upload/Download Test Script

Usage:
    python scripts/multiple-upload_download.py upload
    python scripts/multiple-upload_download.py download
    python scripts/multiple-upload_download.py both

Note:
    Download mac dinh dong goi cac file da tai thanh downloads.zip.
    Upload khong nen.

Requirements:
    pip install minio python-dotenv
"""

import os
import time
import argparse
import zipfile
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()


# ============================================================
# CONFIG
# ============================================================

@dataclass
class StorageConfig:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = False


def load_config() -> StorageConfig:
    return StorageConfig(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123"),
        bucket=os.getenv("MINIO_BUCKET_NAME", "demo-bucket"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    )


# ============================================================
# CLIENT
# ============================================================

def create_client(config: StorageConfig) -> Minio:
    return Minio(
        config.endpoint,
        access_key=config.access_key,
        secret_key=config.secret_key,
        secure=config.secure,
    )


def ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"[OK] Created bucket: {bucket}")
    else:
        print(f"[OK] Bucket exists: {bucket}")


# ============================================================
# TEST FILES
# ============================================================

def create_test_files() -> list[dict]:
    files = []

    txt = Path("test_small.txt")
    txt.write_text("MinIO distributed storage test\n" * 200, encoding="utf-8")
    files.append({"path": str(txt), "desc": "TXT 5.7KB"})

    csv_file = Path("test_data.csv")
    lines = ["id,name,email\n"] + [f"{i},User{i},user{i}@test.com\n" for i in range(1000)]
    csv_file.write_text("".join(lines), encoding="utf-8")
    files.append({"path": str(csv_file), "desc": "CSV 28KB"})

    json_file = Path("test_data.json")
    data = str({"users": [{"id": i, "name": f"User {i}"} for i in range(500)]})
    json_file.write_text(data, encoding="utf-8")
    files.append({"path": str(json_file), "desc": "JSON 16KB"})

    bin_1mb = Path("test_1mb.bin")
    bin_1mb.write_bytes(os.urandom(1024 * 1024))
    files.append({"path": str(bin_1mb), "desc": "BIN 1MB"})

    bin_10mb = Path("test_10mb.bin")
    bin_10mb.write_bytes(os.urandom(10 * 1024 * 1024))
    files.append({"path": str(bin_10mb), "desc": "BIN 10MB"})

    return files


# ============================================================
# CORE LOGIC
# ============================================================

def upload_files(client: Minio, bucket: str, files: list[dict]) -> list[dict]:
    results = []
    for f in files:
        file_path = f["path"]
        file_size = os.path.getsize(file_path)
        object_name = Path(file_path).name

        start = time.time()
        client.fput_object(bucket, object_name, file_path)
        elapsed = time.time() - start

        size_str = f"{file_size/1024:.1f}KB" if file_size < 1024*1024 else f"{file_size/(1024*1024):.1f}MB"
        results.append({
            "file": f["desc"],
            "size": size_str,
            "action": "upload",
            "time": f"{elapsed:.3f}s",
            "status": "OK",
        })
    return results


def download_files(client: Minio, bucket: str, files: list[dict]) -> list[dict]:
    results = []
    for f in files:
        file_path = f["path"]
        object_name = Path(file_path).name
        dl_path = f"downloaded_{object_name}"

        start = time.time()
        client.fget_object(bucket, object_name, dl_path)
        elapsed = time.time() - start

        file_size = os.path.getsize(dl_path)
        size_str = f"{file_size/1024:.1f}KB" if file_size < 1024*1024 else f"{file_size/(1024*1024):.1f}MB"
        results.append({
            "file": f["desc"],
            "size": size_str,
            "action": "download",
            "time": f"{elapsed:.3f}s",
            "status": "OK",
        })

    return results


def zip_downloads(files: list[dict]) -> str:
    zip_name = "downloads.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            local = f"downloaded_{Path(f['path']).name}"
            zf.write(local, arcname=Path(f["path"]).name)

    for f in files:
        Path(f"downloaded_{Path(f['path']).name}").unlink()

    return zip_name


def verify_files(client: Minio, bucket: str, files: list[dict]) -> bool:
    all_ok = True
    for f in files:
        file_path = f["path"]
        object_name = Path(file_path).name
        dl_path = f"verify_{object_name}"

        client.fget_object(bucket, object_name, dl_path)

        original = open(file_path, "rb").read()
        downloaded = open(dl_path, "rb").read()

        if original != downloaded:
            print(f"[FAIL] Mismatch: {object_name}")
            all_ok = False

        os.remove(dl_path)

    return all_ok


def list_objects(client: Minio, bucket: str) -> None:
    print(f"\nObjects in '{bucket}':")
    for obj in client.list_objects(bucket):
        print(f"  - {obj.object_name} ({obj.size} bytes)")


# ============================================================
# REPORT
# ============================================================

def print_report(results: list[dict]) -> None:
    print(f"\n{'File':<15} {'Size':<10} {'Action':<10} {'Time':<10} {'Status'}")
    print("-" * 60)
    for r in results:
        print(f"{r['file']:<15} {r['size']:<10} {r['action']:<10} {r['time']:<10} {r['status']}")


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MinIO Multiple File Upload/Download Test"
    )
    parser.add_argument(
        "command",
        choices=["upload", "download", "both"],
        help="upload = upload only, download = download only, both = upload + download + verify"
    )
    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    args = parse_args()
    config = load_config()
    client = create_client(config)

    try:
        ensure_bucket(client, config.bucket)
        files = create_test_files()
        results = []

        if args.command in ("upload", "both"):
            print("\n--- UPLOAD ---")
            upload_results = upload_files(client, config.bucket, files)
            results.extend(upload_results)
            print_report(upload_results)

        if args.command in ("download", "both"):
            print("\n--- DOWNLOAD ---")
            download_results = download_files(client, config.bucket, files)
            results.extend(download_results)
            print_report(download_results)

            zip_name = zip_downloads(files)
            raw_size = sum(os.path.getsize(f["path"]) for f in files)
            zip_size = os.path.getsize(zip_name)
            saved = (1 - zip_size / raw_size) * 100 if raw_size else 0
            print(f"\n[OK] Zipped {len(files)} file -> {zip_name} "
                  f"({zip_size/1024:.1f}KB / {raw_size/1024:.1f}KB, giam {saved:.0f}%)")

        if args.command == "both":
            print("\n--- VERIFY ---")
            if verify_files(client, config.bucket, files):
                print("[OK] All files verified successfully!")
            else:
                print("[FAIL] Some files mismatch!")

        list_objects(client, config.bucket)

    except S3Error as err:
        print(f"[ERROR] MinIO: {err}")


if __name__ == "__main__":
    main()
