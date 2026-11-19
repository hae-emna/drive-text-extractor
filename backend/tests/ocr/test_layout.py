import pytest

from drive_text_extractor.ocr.layout import TextLine, arrange, mean_confidence


def line(text: str, left: float, top: float, height: float = 20, score: float = 0.9) -> TextLine:
    width = 10 * len(text)
    corners = ((left, top), (left + width, top), (left + width, top + height), (left, top + height))
    return TextLine(text=text, score=score, corners=corners)


def test_lines_are_read_top_to_bottom() -> None:
    lines = [line("second", 0, 30), line("first", 0, 0), line("third", 0, 60)]

    assert arrange(lines) == "first\nsecond\nthird"


def test_lines_side_by_side_form_one_row_read_left_to_right() -> None:
    # A timestamp next to a duration, a few pixels lower: one row.
    lines = [line("0:09", 400, 3), line("0:01", 0, 0)]

    assert arrange(lines) == "0:01 0:09"


def test_a_large_vertical_gap_starts_a_new_paragraph() -> None:
    lines = [line("modern circle", 0, 0), line("café and concept store", 0, 25), line("2", 0, 200)]

    assert arrange(lines) == "modern circle\ncafé and concept store\n\n2"


def test_slanted_text_keeps_its_place() -> None:
    # A sign photographed at an angle: its box rises 30 px from left to right.
    slanted = TextLine(
        text="modern circle",
        score=0.98,
        corners=((0, 130), (300, 100), (300, 125), (0, 155)),
    )

    assert arrange([line("21:09", 0, 0), slanted, line("with us", 0, 300)]) == (
        "21:09\n\nmodern circle\n\nwith us"
    )


def test_two_lines_of_a_slanted_sign_stay_on_separate_rows() -> None:
    # Boxes RapidOCR returned for the cafe screenshot: a sign and its subtitle, both tilted.
    sign = TextLine("modern circle", 0.98, ((4, 387), (389, 479), (372, 550), (0, 458)))
    subtitle = TextLine(
        "café and concept store", 0.97, ((8, 456), (317, 524), (310, 557), (1, 489))
    )

    assert sign.height == pytest.approx(72, abs=1)
    assert arrange([subtitle, sign]) == "modern circle\ncafé and concept store"


def test_text_is_trimmed_and_nothing_gives_an_empty_string() -> None:
    assert arrange([line("  Thank you!  ", 0, 0)]) == "Thank you!"
    assert arrange([]) == ""


def test_confidence_weighs_long_lines_more_than_stray_marks() -> None:
    lines = [line("Modern Circle", 0, 0, score=0.97), line("X", 0, 40, score=0.5)]

    # (13 x 0.97 + 1 x 0.5) / 14
    assert mean_confidence(lines) == pytest.approx(93.6)


def test_confidence_is_none_without_text() -> None:
    assert mean_confidence([]) is None
    assert mean_confidence([line("   ", 0, 0)]) is None
