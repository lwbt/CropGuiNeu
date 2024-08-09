#!/usr/bin/python3

# cspell:ignore imread dtype itemsize

import argparse
import cv2
from PIL import Image, JpegImagePlugin

from crop_gui_neu.jpeg_quality import JpegQuality


def get_image_attributes(image_path):
    """
    Extracts image attributes from the specified image path.

    Args:
        image_path (str): Path to the image file.

    Returns:
        dict: A dictionary containing image attributes.
    """

    image = cv2.imread(image_path)

    if image is None:
        return None

    height, width, channels = image.shape
    bits_per_sample = image.dtype.itemsize * 8
    color_components = "BGR" if channels == 3 else "Grayscale"

    pim = Image.open(image_path)

    image_info = JpegQuality()
    quality = image_info.get_quality(image_path)

    sub_sampling = JpegImagePlugin.get_sampling(pim)

    match sub_sampling:
        case 0:
            sub_sampling = "4:4:4"
        case 1:
            sub_sampling = "4:2:2"
        case 2:
            sub_sampling = "4:2:0"

    attributes = {
        "width": width,
        "height": height,
        "bits_per_sample": bits_per_sample,
        "color_components": color_components,
        "quality": quality,
        "sub_sampling": sub_sampling,
    }

    return attributes


def print_aligned_attributes(attributes, column_width=20):
    for key, value in attributes.items():
        key_length = len(key)
        spaces = column_width - key_length - 2  # Adjust for colon and space
        print(f"{key}:{spaces * ' '} {value}")


def main():
    parser = argparse.ArgumentParser(description="Print image attributes")
    parser.add_argument("image_path", type=str, help="Path to the image file")
    args = parser.parse_args()

    attributes = get_image_attributes(args.image_path)

    if attributes:
        print_aligned_attributes(attributes)
    else:
        print(f"Error: Could not read image from {args.image_path}")


if __name__ == "__main__":
    main()
