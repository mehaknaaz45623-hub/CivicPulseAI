from io import BytesIO

import torch
from PIL import Image, UnidentifiedImageError
from transformers import CLIPModel, CLIPProcessor


MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

MODEL_NAME = "openai/clip-vit-base-patch32"

model = None
processor = None


def load_model():
    global model, processor

    if model is None or processor is None:
        print("Loading CivicPulse AI image recognition model...")

        processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        model = CLIPModel.from_pretrained(MODEL_NAME)
        model.eval()

        print("Image recognition model loaded successfully!")


def validate_image(image_bytes):

    if not image_bytes:
        raise ValueError("No image was uploaded")

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise ValueError("Image must be smaller than 5 MB")

    try:
        image = Image.open(BytesIO(image_bytes))

        if image.format not in ALLOWED_FORMATS:
            raise ValueError(
                "Only JPG, PNG and WEBP images are supported"
            )

        image.verify()

        return {
            "valid": True,
            "size_bytes": len(image_bytes),
            "message": "Image uploaded successfully"
        }

    except (UnidentifiedImageError, OSError):
        raise ValueError("Invalid or corrupted image")


def analyze_image_bytes(image_bytes):

    validation = validate_image(image_bytes)

    load_model()

    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    labels = [
        "a photograph of a road pothole",
        "a photograph of garbage dumped on a street",
        "a photograph of a damaged road",
        "a photograph of an overflowing drain",
        "a photograph of a broken streetlight",
        "a photograph of a water leakage problem",
        "a photograph of an ordinary street"
    ]

    inputs = processor(
        text=labels,
        images=image,
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)

        probabilities = outputs.logits_per_image.softmax(
            dim=1
        )[0]

    best_index = int(torch.argmax(probabilities))

    return {
        "valid": validation["valid"],
        "predicted_issue": labels[best_index],
        "confidence": round(
            float(probabilities[best_index]) * 100,
            2
        ),
        "all_predictions": {
            labels[index]: round(
                float(probabilities[index]) * 100,
                2
            )
            for index in range(len(labels))
        }
    }