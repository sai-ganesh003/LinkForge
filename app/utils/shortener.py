import string
import random
from app.models import URL

CHARACTERS = string.ascii_letters + string.digits

def generate_short_code(length=6):
    while True:
        code = ''.join(random.choices(CHARACTERS, k=length))
        if not URL.query.filter_by(short_code=code).first():
            return code