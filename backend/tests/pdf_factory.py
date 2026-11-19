"""Build tiny but valid PDFs in memory, so tests need no binary fixtures in the repository."""

from collections.abc import Sequence


def make_pdf(pages: Sequence[str | None], page_size: tuple[int, int] = (612, 792)) -> bytes:
    """One entry per page: its text (``\\n`` starts a new line), or ``None`` for a blank page.

    Text uses the standard Helvetica font, so it must be Latin-1. ``page_size`` is in points.
    """
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    kids: list[str] = []
    for index, text in enumerate(pages):
        page_id, content_id = 4 + 2 * index, 5 + 2 * index
        kids.append(f"{page_id} 0 R")
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_size[0]} {page_size[1]}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode()
        stream = _content_stream(text)
        objects[content_id] = b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream)
    objects[2] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode()

    out = bytearray(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}
    for number in sorted(objects):
        offsets[number] = len(out)
        out += b"%d 0 obj\n%s\nendobj\n" % (number, objects[number])
    xref_offset = len(out)
    size = max(objects) + 1
    out += b"xref\n0 %d\n0000000000 65535 f \n" % size
    for number in range(1, size):
        out += b"%010d 00000 n \n" % offsets[number]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (size, xref_offset)
    return bytes(out)


def _content_stream(text: str | None) -> bytes:
    if not text:
        return b""
    shows = []
    for line in text.split("\n"):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        shows.append(f"({escaped}) Tj T*")
    return f"BT /F1 12 Tf 14 TL 72 720 Td {' '.join(shows)} ET".encode("latin-1")
