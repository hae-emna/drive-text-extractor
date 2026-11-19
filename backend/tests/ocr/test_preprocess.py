import io

import pytest
from PIL import Image

from drive_text_extractor.ocr.preprocess import MAX_UPSCALE, prepare_for_ocr
from tests.images import encode

EXIF_ORIENTATION = 0x0112
ROTATED_90_CW = 6


def test_output_is_grayscale() -> None:
    assert prepare_for_ocr(Image.new("RGB", (2400, 1200), "white")).mode == "L"


def test_transparent_background_becomes_white_not_black() -> None:
    transparent = Image.new("RGBA", (2400, 1200), (0, 0, 0, 0))

    prepared = prepare_for_ocr(transparent)

    assert prepared.getpixel((10, 10)) == 255


def test_small_images_are_upscaled_towards_the_target_size() -> None:
    assert prepare_for_ocr(Image.new("L", (800, 400), 255)).size == (1600, 800)


def test_upscaling_is_capped() -> None:
    prepared = prepare_for_ocr(Image.new("L", (100, 50), 255))

    assert prepared.size == (int(100 * MAX_UPSCALE), int(50 * MAX_UPSCALE))


@pytest.mark.parametrize("size", [(1000, 700), (1654, 2339), (3000, 2000)])
def test_images_at_scan_resolution_keep_their_size(size: tuple[int, int]) -> None:
    assert prepare_for_ocr(Image.new("L", size, 255)).size == size


def test_exif_orientation_is_applied() -> None:
    exif = Image.Exif()
    exif[EXIF_ORIENTATION] = ROTATED_90_CW
    photo = Image.open(io.BytesIO(encode(Image.new("RGB", (2400, 1200)), "JPEG", exif=exif)))

    prepared = prepare_for_ocr(photo)

    assert prepared.size == (1200, 2400)
