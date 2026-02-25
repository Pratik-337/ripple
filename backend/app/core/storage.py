import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

_s3_client = None


def get_s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
    return _s3_client


def ensure_bucket_exists() -> None:
    s3 = get_s3()
    try:
        s3.head_bucket(Bucket=settings.aws_s3_bucket)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            s3.create_bucket(Bucket=settings.aws_s3_bucket)
            # Make bucket public-read so presigned GET URLs work from the browser
            s3.put_bucket_policy(
                Bucket=settings.aws_s3_bucket,
                Policy=f"""{{
                    "Version":"2012-10-17",
                    "Statement":[{{
                        "Effect":"Allow",
                        "Principal":"*",
                        "Action":"s3:GetObject",
                        "Resource":"arn:aws:s3:::{settings.aws_s3_bucket}/*"
                    }}]
                }}""",
            )
        else:
            raise


def generate_presigned_upload_url(s3_key: str, expires_in: int = 3600) -> str:
    s3 = get_s3()
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.aws_s3_bucket, "Key": s3_key},
        ExpiresIn=expires_in,
    )


def generate_presigned_download_url(s3_key: str, expires_in: int = 3600) -> str:
    s3 = get_s3()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.aws_s3_bucket, "Key": s3_key},
        ExpiresIn=expires_in,
    )


def upload_bytes(s3_key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    s3 = get_s3()
    s3.put_object(
        Bucket=settings.aws_s3_bucket,
        Key=s3_key,
        Body=data,
        ContentType=content_type,
    )


def download_bytes(s3_key: str) -> bytes:
    s3 = get_s3()
    response = s3.get_object(Bucket=settings.aws_s3_bucket, Key=s3_key)
    return response["Body"].read()


def delete_object(s3_key: str) -> None:
    s3 = get_s3()
    s3.delete_object(Bucket=settings.aws_s3_bucket, Key=s3_key)
