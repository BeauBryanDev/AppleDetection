import boto3
import os
from botocore.exceptions import ClientError
from app.core.logging import logger


def get_s3_client():
    """ return s3 client set with env credentials"""
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def upload_image_to_s3(image_bytes: bytes, filename: str) -> str:
    """
        Upload an image to S3 and return the relative path to save it to the database.

        Args:

        image_bytes: Bytes of the processed image

        filename: Unique filename (uuid_original.jpg)

        Returns:

        str: Relative path like 'uploads/uuid_filename.jpg'
        Same format as above for database compatibility.

        Raises:

        Exception: If the upload to S3 fails
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        raise ValueError("S3_BUCKET_NAME not defined in the environment variables")

    s3_key = f"uploads/{filename}"

    try:
        client = get_s3_client()
        client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=image_bytes,
            ContentType="image/jpeg",
        )
        logger.info(f"Imagen subida a S3: s3://{bucket}/{s3_key}")
        return s3_key

    except ClientError as e:
        logger.error(f"Error subiendo imagen a S3: {e}")
        raise Exception(f"Error subiendo imagen a S3: {e}")


def get_presigned_url(s3_key: str, expiration_seconds: int = 3600) -> str:
    """
        Generates a pre-signed URL to access a private image in S3.

        Args:

        s3_key: Path to the object in S3 (e.g., 'uploads/uuid_filename.jpg')

        expiration_seconds: URL validity period (default: 1 hour)

        Returns:

        str: Temporary pre-signed URL
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    try:
        client = get_s3_client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expiration_seconds,
        )
        return url
    except ClientError as e:
        logger.error(f" Error generating pre-signed URL: {e}")
        raise Exception(f"Error generating pre-signed URL: {e}")


def delete_image_from_s3(s3_key: str) -> bool:
    """
        Delete an image from S3. Args: s3 key: Path of the object in S3 
        Returns: bool: True if it was deleted successfully
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    try:
        client = get_s3_client()
        client.delete_object(Bucket=bucket, Key=s3_key)
        logger.info(f"Imagen eliminada de S3: {s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Error eliminando imagen de S3: {e}")
        return False


def s3_is_configured() -> bool:
    """
        Validate iif S3 is configured in the environment.
Enable fallback to local storage if it is not.
    """
    return all([
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("S3_BUCKET_NAME"),
    ])
