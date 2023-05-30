import random

from PIL import Image
import requests
from io import BytesIO
import base64


class Background:
    counter = 0

    def __init__(self, width=800, height=800, rotate=True, flip=True, modification_pct=40):
        counter = random.randint(0, 100000)
        response = requests.get(f"https://source.unsplash.com/random/{width}x{height}?store,boxes?sig={counter}")
        self._image = Image.open(BytesIO(response.content))
        self._rotate = rotate
        self._flip = flip
        self._modification_pct = modification_pct

    @property
    def image(self):
        from PIL import Image

        image = self._image
        width, height = image.width, image.height
        if self._flip and (random.randint(0, 100) < self._modification_pct):
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if self._flip and (random.randint(0, 100) < self._modification_pct):
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        if self._rotate and (random.randint(0, 100) < self._modification_pct):
            # TODO: Make a smarter rotation
            image = image.rotate(random.randint(0, 360), resample=Image.Resampling.NEAREST, expand=True)

        return image.resize((width, height))

    def _repr_html_(self):
        buffered = BytesIO()
        self.image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"<img src='data:image/jpeg;base64, {img_str}'></img>"