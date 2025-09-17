import tempfile, boto3
from pdf2image import convert_from_bytes
import pytesseract
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from packages.shared.env import settings
from packages.shared.models import Slide

engine = create_engine(settings.DATABASE_URL); Session = sessionmaker(engine)
s3 = boto3.client("s3", endpoint_url=settings.S3_ENDPOINT,
                  aws_access_key_id=settings.S3_ACCESS_KEY,
                  aws_secret_access_key=settings.S3_SECRET_KEY)

def ocr_pdf(meeting_id: str, key: str):
    obj = s3.get_object(Bucket=settings.S3_BUCKET_RAW, Key=key)
    pdf_bytes = obj["Body"].read()
    images = convert_from_bytes(pdf_bytes, dpi=200)
    with Session() as db:
        for i, img in enumerate(images, start=1):
            text = pytesseract.image_to_string(img)
            slide_key = f"derived/{meeting_id}/slide_{i}.png"
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            img.save(tmp)
            s3.upload_file(tmp, settings.S3_BUCKET_DERIVED, slide_key)
            db.add(Slide(meeting_id=meeting_id, page=i, ocr_text=text, storage_key=slide_key))
        db.commit()
