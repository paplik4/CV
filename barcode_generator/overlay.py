import random
from typing import List

from PIL import ImageDraw, Image
from PIL.Image import Image as PilImage
import cv2
import numpy as np
from collections import namedtuple
from shapely.geometry import Polygon

Coord = namedtuple("Coord", ["x", "y"])


class BBox:
    def __init__(self, width, height, x0, y0, x1, y1, rotation=0):
        self.corners = [
            Coord(x=x0, y=y0),
            Coord(x=x0, y=y1),
            Coord(x=x1, y=y1),
            Coord(x=x1, y=y0),
        ]
        self.shape = Polygon(self.corners)

        self.width = width
        self.height = height
        self.center = Coord(x=x0 + ((x1 - x0) / 2), y=y0 + ((y1 - y0) / 2))
        self.rotation = rotation
 

    @property
    def x0(self):
        return min([corner.x for corner in self.corners])

    @property
    def x1(self):
        return max([corner.x for corner in self.corners])

    @property
    def y0(self):
        return min([corner.y for corner in self.corners])

    @property
    def y1(self):
        return max([corner.y for corner in self.corners])

    def overlaps(self, other):
        return self.shape.overlaps(other.shape)

    def rotate(self, angle):
        M = cv2.getRotationMatrix2D((self.center.x, self.center.y), angle, 1.0)
        cos, sin = abs(M[0, 0]), abs(M[0, 1])
        new_width = int((self.height * sin) + (self.width * cos))
        new_height = int((self.height * cos) + (self.width * sin))
        M[0, 2] += (new_width / 2) - self.center.x
        M[1, 2] += (new_height / 2) - self.center.y

        new_corners = []
        for corner in self.corners:
            v = [corner.x, corner.y, 1]
            adjusted = np.dot(M, v)
            new_corners.append(Coord(x=int(adjusted[0]), y=int(adjusted[1])))

        self.corners = new_corners
        self.width = new_width
        self.height = new_height
        self.rotation += angle
        return self

    def move(self, x, y):
        self.center = Coord(x = self.center.x + x, y = self.center.y + y)
        self.corners = [Coord(x=corner.x + x, y=corner.y + y) for corner in self.corners]
        return self

    def placement(self, x, y):
        return BBox(self.width, self.height, self.x0, self.y0, self.x1, self.y1).move(x, y)

    def dict(self):
        return {
            "corners": list(map(tuple, self.corners)),
            "center": tuple(self.center),
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
            "xmin" : self.x0,
            "ymin" : self.y0,
            "xmax" : self.x1,
            "ymax" : self.y1
        }


class Overlay:
    def __init__(self, image: PilImage):
        self.image = image.convert("RGBA")
        self.rotation = 0
        self.x = 0
        self.y = 0
        self.corners = BBox(image.width, image.height, 0, 0, image.width, image.height)
        self.placed = False

    @property
    def bbox(self):
        return BBox(self.image.width, self.image.height, self.x, self.y, self.x + self.image.width, self.y + self.image.height)

    def rotate(self, degrees):
        if self.placed:
            raise RuntimeError("Placed Overlay is immutable")

        self.image = self.image.rotate(degrees, expand=True, fillcolor=(0, 0, 0, 0))
        self.corners.rotate(degrees)
        self.rotation += degrees
        return self

    def insert(self, image: PilImage, x, y) -> PilImage:
        if self.placed:
            raise RuntimeError("Overlay can only be placed once")
        else:
            self.placed = True

        # Translate the image into its position in the background image
        self.x = x
        self.y = y
        self.corners.move(x, y)

        # Generate the resulting image and placement information
        image = image.convert('RGBA')
        image.paste(self.image, (x, y), self.image)
        return image

    def overlaps(self, other):
        # TODO: NOT IMPLEMENTED
        raise NotImplementedError

    def position(self, image, overlays: List['Overlay'], attempts = 1):
        # TODO: CHECK FOR OVERLAPS
        return (
            random.randint(0, image.width - self.bbox.width - 1),
            random.randint(0, image.height - self.bbox.height - 1)
        )

    def show(self):
        width, height = (self.image.width * 2, self.image.height * 2)
        image = Image.new('RGBA', (width, height), (0,0,0,0))
        offset = (int((width - self.image.width) // 2), int((height - self.image.height) // 2))
        image = self.insert(image, *offset)
        draw = ImageDraw.Draw(image)
        draw.polygon(self.corners.corners, outline=(0, 255, 0))
        draw.polygon(self.bbox.corners, outline=(255, 0, 0))
        return image

    def dict(self):
        return {
            "width": self.bbox.width,
            "height": self.bbox.height,
            "rotation": self.rotation,
            "bbox": self.bbox.dict(),
            "corners": self.corners.dict()
        }