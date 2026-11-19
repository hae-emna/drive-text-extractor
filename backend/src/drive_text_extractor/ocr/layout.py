"""Turn text lines detected anywhere in an image into plain text in reading order.

Scene-text engines return one box per line of text, wherever it is: a shop sign, a caption, a
timestamp in a corner. Boxes whose vertical centres line up are on the same row and are joined
left to right; a gap between rows taller than a typical line becomes a paragraph break, so
separate pieces of text do not run together.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from math import dist
from statistics import fmean, median

Point = tuple[float, float]

SAME_ROW = 0.5
"""Two lines are on the same row when their centres are closer than this share of a line height."""

PARAGRAPH_GAP = 1.0
"""Rows further apart than this many typical line heights are separated by a blank line."""


@dataclass(frozen=True, slots=True)
class TextLine:
    text: str
    score: float
    """Recognition confidence, 0 to 1."""
    corners: tuple[Point, ...]
    """The corners of the line's box in image pixels, clockwise from the top left.
    Slanted text, such as a sign photographed at an angle, gives a slanted box."""

    @property
    def top(self) -> float:
        return min(y for _, y in self.corners)

    @property
    def bottom(self) -> float:
        return max(y for _, y in self.corners)

    @property
    def left(self) -> float:
        return min(x for x, _ in self.corners)

    @property
    def height(self) -> float:
        """The height of the text itself, measured along the box's left and right edges.

        The upright extent of a slanted box is much larger than its text, and would make two
        lines of a slanted sign look like one row.
        """
        if len(self.corners) != 4:
            return self.bottom - self.top
        top_left, top_right, bottom_right, bottom_left = self.corners
        return (dist(top_left, bottom_left) + dist(top_right, bottom_right)) / 2

    @property
    def middle(self) -> float:
        return fmean(y for _, y in self.corners)


def arrange(lines: Sequence[TextLine]) -> str:
    rows = _rows(lines)
    if not rows:
        return ""
    typical_height = median(line.height for line in lines)

    parts: list[str] = []
    previous: list[TextLine] | None = None
    for row in rows:
        if previous is not None and _top(row) - _bottom(previous) > PARAGRAPH_GAP * typical_height:
            parts.append("")
        parts.append(" ".join(line.text.strip() for line in sorted(row, key=lambda x: x.left)))
        previous = row
    return "\n".join(parts)


def mean_confidence(lines: Sequence[TextLine]) -> float | None:
    """Recognition confidence (0-100), weighted by length so a stray symbol weighs little."""
    weighted = [(len(line.text.strip()), line.score) for line in lines if line.text.strip()]
    total = sum(length for length, _ in weighted)
    if total == 0:
        return None
    return round(100 * sum(length * score for length, score in weighted) / total, 1)


def _rows(lines: Sequence[TextLine]) -> list[list[TextLine]]:
    rows: list[list[TextLine]] = []
    for line in sorted(lines, key=lambda x: x.middle):
        if rows:
            row = rows[-1]
            centre = fmean(member.middle for member in row)
            tolerance = SAME_ROW * min(line.height, median(member.height for member in row))
            if abs(line.middle - centre) <= tolerance:
                row.append(line)
                continue
        rows.append([line])
    return rows


def _top(row: list[TextLine]) -> float:
    return min(line.top for line in row)


def _bottom(row: list[TextLine]) -> float:
    return max(line.bottom for line in row)
