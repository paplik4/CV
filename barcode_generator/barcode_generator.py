from typing import Union, Optional
import random
from io import BytesIO
import tempfile

import barcode
from barcode.writer import SVGWriter

from PIL import Image
from reportlab.graphics.renderPM import drawToPIL
from svglib.svglib import svg2rlg


class Barcode:
    MAP = {
        # Possible barcode providers: 'code128', 'code39', 'ean', 'ean13', 'ean14', 'ean8', 'gs1', 'gs1_128', 'gtin', 'isbn', 'isbn10', 'isbn13', 'issn', 'itf', 'jan', 'pzn', 'upc', 'upca'
        'ean13': lambda: str(random.randint(1000000000000, 9999999999999))
    }

    def __init__(self, uid: Optional[Union[str, int]] = None, provider: Optional[str] = None):
        self._uid = uid
        self._provider = provider
        self._svg = None

    @property
    def uid(self):
        if self._uid is None:
            self._uid = Barcode.MAP[self.provider]()
        return str(self._uid)

    @property
    def provider(self):
        if self._provider is None:
            self._provider = random.choice(list(Barcode.MAP.keys()))
        return self._provider

    @property
    def svg(self):
        if self._svg is None:
            buffer = BytesIO()  # Generate a Byte buffer
            GEN_BARCODE = barcode.get_barcode_class(self.provider)
            GEN_BARCODE(self.uid, writer=SVGWriter()).write(buffer)  # write the SVG image to the buffer
            self._svg = buffer.getvalue().decode('UTF-8')

        return self._svg

    def image(self, width, height):
        def scale(w, h, x, y, maximum=True):
            nw = y * w / h
            nh = x * h / w
            if maximum ^ (nw >= x):
                return nw or 1, y
            return x, nh or 1

        with tempfile.NamedTemporaryFile("w") as tmp:
            with open(tmp.name, "w") as fp:
                fp.write(self.svg)

            svg = svg2rlg(tmp.name)

        old_width, old_height = svg.width, svg.height
        new_width, new_height = scale(svg.width, svg.height, width, height)

        svg.scale(new_width / old_width, new_height / old_height)
        svg.width = new_width
        svg.height = new_height

        image = Image.new('RGB', (width, height), (255, 255, 255))
        offset = (int((width - svg.width) // 2), int((height - svg.height) // 2))
        image.paste(drawToPIL(svg), offset)

        return image

    def __str__(self):
        return self.svg

    def display(self):
        from IPython.display import SVG, display
        display(SVG(data=self.svg))

    def _repr_html_(self):
        return "\n".join(self.svg.split("\n")[4:])

#%%
