from __future__ import annotations

import os
from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


def _uses_s3() -> bool:
    return settings.resume_storage_backend in {"s3", "neon"}


@lru_cache(maxsize=1)
def _s3_client():
    required = {
        "AWS_REGION": settings.aws_region,
        "AWS_ENDPOINT_URL_S3": settings.aws_endpoint_url_s3,
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError("Object storage configuration is incomplete: " + ", ".join(missing))
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url_s3,
        aws_access_key_id=required["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=required["AWS_SECRET_ACCESS_KEY"],
        config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 3, "mode": "standard"}),
    )


def save_resume(key: str, content: bytes, content_type: str) -> None:
    if _uses_s3():
        _s3_client().put_object(
            Bucket=settings.resume_storage_bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return
    path = settings.resume_storage_dir / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def read_resume(key: str) -> bytes | None:
    if _uses_s3():
        try:
            result = _s3_client().get_object(Bucket=settings.resume_storage_bucket, Key=key)
            return result["Body"].read()
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"NoSuchKey", "NoSuchBucket", "404", "NotFound"}:
                return None
            raise
    path = settings.resume_storage_dir / key
    return path.read_bytes() if path.is_file() else None


def delete_resume(key: str) -> None:
    if _uses_s3():
        _s3_client().delete_object(Bucket=settings.resume_storage_bucket, Key=key)
        return
    (settings.resume_storage_dir / key).unlink(missing_ok=True)



def check_resume_storage() -> None:
    if _uses_s3():
        _s3_client().list_objects_v2(Bucket=settings.resume_storage_bucket, MaxKeys=1)
        return
    settings.resume_storage_dir.mkdir(parents=True, exist_ok=True)
