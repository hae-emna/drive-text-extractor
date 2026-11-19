"""Generate the sample folder used for the demo mode and for the public test Drive folder.

Each file exercises one path of the pipeline: native PDF, scanned PDF, mixed PDF, images in
English, French and Arabic, a rotated scan, a damaged PDF and an unsupported file.

Arabic needs a font with Arabic glyphs and Pillow built with libraqm (text shaping), which the
Docker image has:

    docker compose run --rm -v ./samples:/samples app python scripts/make_samples.py /samples/input
"""

import argparse
import io
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

INVOICE_PAGES = [
    [
        "FACTURE / INVOICE No 2026-0142",
        "Date : 12 novembre 2026",
        "Client : Société Atlas, Nabeul, Tunisie",
        "",
        "Désignation                      Montant",
        "Audit de sécurité cloud          1 800,000 TND",
        "Support mensuel                    450,000 TND",
        "",
        "Total TTC : 2 250,000 TND",
    ],
    [
        "Conditions de paiement",
        "Paiement à 30 jours par virement bancaire.",
        "Payment terms: 30 days by bank transfer.",
    ],
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONTS:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise SystemExit("No TrueType font found; run this script in the Docker image.")


def scanned_page(lines: list[str], *, rtl: bool = False, font_size: int = 42) -> Image.Image:
    """A grayscale 'scan' of an A4-ish page: text, slight blur, off-white paper."""
    width, height = 1654, 2339  # A4 at 200 DPI
    page = Image.new("L", (width, height), color=248)
    draw = ImageDraw.Draw(page)
    face = font(font_size)
    y = 180
    for line in lines:
        if rtl:
            draw.text(
                (width - 150, y),
                line,
                font=face,
                fill=20,
                anchor="ra",
                direction="rtl",
                language="ar",
            )
        else:
            draw.text((150, y), line, font=face, fill=20)
        y += int(font_size * 1.9)
    return page.filter(ImageFilter.GaussianBlur(0.6))


def native_pdf(pages: list[list[str]]) -> bytes:
    """A minimal PDF with a real text layer (Helvetica, Windows-1252 encoding)."""
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    }
    kids = []
    for index, lines in enumerate(pages):
        page_id, content_id = 4 + 2 * index, 5 + 2 * index
        kids.append(f"{page_id} 0 R")
        shows = " ".join(f"({_escape(line)}) Tj T*" for line in lines)
        stream = f"BT /F1 13 Tf 20 TL 60 780 Td {shows} ET".encode("cp1252")
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode()
        objects[content_id] = b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream)
    objects[2] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode()

    out = bytearray(b"%PDF-1.4\n")
    offsets = {}
    for number in sorted(objects):
        offsets[number] = len(out)
        out += b"%d 0 obj\n%s\nendobj\n" % (number, objects[number])
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for number in sorted(objects):
        out += b"%010d 00000 n \n" % offsets[number]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def _escape(line: str) -> str:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def scanned_pdf(pages: list[Image.Image]) -> bytes:
    buffer = io.BytesIO()
    first, *rest = pages
    first.save(buffer, format="PDF", resolution=200, save_all=True, append_images=rest)
    return buffer.getvalue()


def merge_pdfs(*documents: bytes) -> bytes:
    merged = pdfium.PdfDocument.new()
    for data in documents:
        source = pdfium.PdfDocument(data)
        merged.import_pages(source)
        source.close()
    buffer = io.BytesIO()
    merged.save(buffer)
    merged.close()
    return buffer.getvalue()


def png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def jpeg(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=80)
    return buffer.getvalue()


def build(output: Path) -> None:
    if not features.check("raqm"):
        raise SystemExit("Pillow lacks libraqm: Arabic would be rendered unshaped.")
    output.mkdir(parents=True, exist_ok=True)

    contract = scanned_page(
        [
            "SERVICE AGREEMENT",
            "This agreement is made in Nabeul on 3 November 2026",
            "between the Provider and the Client named below.",
            "The Provider will host and monitor the Client's",
            "document processing platform for twelve months.",
            "Signed by both parties.",
        ]
    )
    annex = scanned_page(
        [
            "ANNEX A - Service levels",
            "Availability target: 99.5 percent per month",
            "Response time for critical incidents: 2 hours",
        ]
    )

    files: dict[str, bytes] = {
        "invoice-native.pdf": native_pdf(INVOICE_PAGES),
        "contract-scanned.pdf": scanned_pdf([contract]),
        "report-mixed.pdf": merge_pdfs(
            native_pdf([["Quarterly report Q3 2026", "Typed summary page with a text layer."]]),
            scanned_pdf([annex]),
        ),
        "receipt-english.png": png(
            scanned_page(
                ["RECEIPT", "Coffee and pastries   18.500 TND", "Paid by card", "Thank you!"],
                font_size=48,
            ).crop((0, 0, 1654, 900))
        ),
        "facture-francais.jpg": jpeg(
            scanned_page(
                [
                    "Bon de livraison n° 88",
                    "Livré le 14 novembre 2026 à Hammamet",
                    "Reçu en bon état par le client.",
                ],
                font_size=46,
            ).crop((0, 0, 1654, 800))
        ),
        "avis-arabe.png": png(
            scanned_page(
                [
                    "إشعار للعملاء",
                    "سيتم إغلاق المكتب يوم الجمعة",
                    "شكرا على تفهمكم",
                ],
                rtl=True,
                font_size=36,
            ).crop((0, 0, 1654, 800))
        ),
        "scan-rotated.jpg": jpeg(
            scanned_page(
                [
                    "Delivery note 2026-77",
                    "This page was scanned sideways",
                    "and must be straightened before OCR.",
                    "Received by the warehouse team.",
                ]
            )
            .crop((0, 0, 1654, 1000))
            .rotate(90, expand=True, fillcolor=248)
        ),
        "corrupted.pdf": native_pdf(INVOICE_PAGES)[:300],
        "notes.txt": b"Text files are listed as skipped: only PDF, PNG and JPEG are processed.\n",
    }
    for name, data in files.items():
        (output / name).write_bytes(data)
        print(f"{name:24} {len(data) / 1000:8.1f} KB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("output", type=Path, help="folder to write the sample files to")
    build(parser.parse_args().output)
