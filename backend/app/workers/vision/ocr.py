from __future__ import annotations

import tempfile

import boto3
import pytesseract
from backend.packages.shared.env import settings
from backend.packages.shared.models import Slide
from pdf2image import convert_from_bytes

from app.core.db import SessionLocal
from app.core.logger import get_logger

log = get_logger(__name__)

s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name=getattr(settings, "S3_REGION", None),
)


def ocr_pdf_bytes(meeting_id: int, pdf_bytes: bytes) -> int:
    """
    Convert PDF bytes to images, OCR them, and store OCR text and the slide image in S3 and DB.
    Returns the number of pages processed.
    """
    pages = convert_from_bytes(pdf_bytes)

    with SessionLocal() as db:
        for i, img in enumerate(pages, start=1):
            text = pytesseract.image_to_string(img)
            slide_key = f"derived/{meeting_id}/slide_{i}.png"

            # Save image to a secure temporary file and upload to S3
            with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
                img.save(tmp.name)
                s3.upload_file(tmp.name, settings.S3_BUCKET_DERIVED, slide_key)

            db.add(
                Slide(
                    meeting_id=meeting_id,
                    page_num=i,
                    ocr_text=text,
                    storage_key=slide_key,
                ),
            )

        db.commit()

    log.info("OCR complete", extra={"meeting_id": meeting_id, "pages": len(pages)})
    return len(pages)

