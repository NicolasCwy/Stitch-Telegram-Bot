import cv2
import numpy as np
import PIL
import sys
from PIL import Image

# rembg
from rembg.bg import remove

file = '' # TYPE IN FILENAME HERE

def removeBG(file):
    """
        from https://github.com/danielgatis/rembg
        To run Rembg

        In App.py
        sys.stdout.buffer.write(remove(sys.stdin.buffer.read()))

        Then run
        cat input.png | python app.py > out.png


        This is an attempt to remove the use of shell and only execute code from python files

        file: path of image to process
        edits file in place and resizes it to 512 x 512 pixels and converts file to png
        """
    # path of output file
    path = "img/out.png"
    sys.stdout = open(path, 'w')

    # open file in binary format to be given to remove function from rembg module
    # equivalent to format produced by sys.stdin.buffer.read()
    with open(file, 'rb') as f:
        contents = f.read()
    sys.stdout.buffer.write(remove(contents))

    return path


def resize(file, origName):
    img = PIL.Image.open(file)
    img = img.resize((512, 512))
    img.save('img/r_' + origName.split('.')[0].split('/')[1] + '.png')
    return img


def processImg(file):
    path = removeBG(file)
    stickerImg = resize(path, file)
    return stickerImg