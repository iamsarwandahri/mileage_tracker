from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def compress_image(image):
    img = Image.open(image)
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=60)
    return ContentFile(buffer.getvalue())

def is_supervisor(user):
    return user.groups.filter(name='Supervisor').exists()

