from io import BytesIO
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile


def create_default_avatar(name):
    image = Image.new("RGB", (256, 256), "#65758B")
    draw = ImageDraw.Draw(image)
    font_path = (
        settings.BASE_DIR
        / "static"
        / "fonts"
        / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
    )
    font = ImageFont.truetype(font_path, 128)
    initial = (name or "?")[0].upper()
    draw.text((128, 128), initial, font=font, fill="white", anchor="mm")

    output = BytesIO()
    image.save(output, format="PNG")
    return ContentFile(output.getvalue(), name=f"avatar_{uuid4().hex}.png")
