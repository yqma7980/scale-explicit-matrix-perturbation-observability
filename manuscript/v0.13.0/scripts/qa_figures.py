import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'figures'
QA = ROOT / 'qa'
QA.mkdir(parents=True, exist_ok=True)


EXPECTED_HEIGHT_MM = {
    'F1_assessment_sequence': 112.0,
    'F2_mixed_field_tangent_anatomy': 100.0,
    'F3_directional_response': 104.0,
    'F4_coordinate_transformation': 94.0,
    'F5_two_reference_contracts': 118.0,
    'F6_effectivity_dependence': 132.0,
    'F7_route_error_mechanism': 132.0,
    'F8_two_operator_route_qualification': 128.0,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest().upper()


def inspect_pdf(path: Path) -> dict:
    document = fitz.open(path)
    if document.page_count != 1:
        raise RuntimeError(f'{path.name}: expected one page, found {document.page_count}')
    page = document[0]
    width_mm = page.rect.width * 25.4 / 72.0
    height_mm = page.rect.height * 25.4 / 72.0
    spans = []
    outside = []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                text = span.get('text', '').strip()
                if not text:
                    continue
                item = {
                    'text': text,
                    'size_pt': float(span['size']),
                    'font': span.get('font', ''),
                    'bbox': [float(value) for value in span['bbox']],
                }
                spans.append(item)
                x0, y0, x1, y1 = item['bbox']
                if x0 < -0.25 or y0 < -0.25 or x1 > page.rect.width + 0.25 or y1 > page.rect.height + 0.25:
                    outside.append(item)
    matrix = fitz.Matrix(200 / 72.0, 200 / 72.0)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    render_path = QA / f'{path.stem}_pdf_render.png'
    pixmap.save(render_path)
    fonts = sorted({font[3] for font in page.get_fonts(full=True)})
    under_six = [span for span in spans if span['size_pt'] < 5.9]
    under_seven = [span for span in spans if span['size_pt'] < 7.0]
    return {
        'file': path.name,
        'sha256': sha256(path),
        'width_mm': width_mm,
        'height_mm': height_mm,
        'expected_width_mm': 190.0,
        'expected_height_mm': EXPECTED_HEIGHT_MM[path.stem],
        'dimension_pass': abs(width_mm - 190.0) <= 0.25
        and abs(height_mm - EXPECTED_HEIGHT_MM[path.stem]) <= 0.25,
        'text_span_count': len(spans),
        'minimum_text_size_pt': min((span['size_pt'] for span in spans), default=None),
        'spans_below_5p9_pt': under_six,
        'spans_below_7_pt': under_seven,
        'out_of_page_text': outside,
        'font_names': fonts,
        'type3_font_name_detected': any('Type3' in font for font in fonts),
        'render': render_path.name,
    }


def make_contact_sheet(records: list[dict]) -> Path:
    cards = []
    for record in records:
        image = Image.open(QA / record['render']).convert('RGB')
        image.thumbnail((1100, 720), Image.Resampling.LANCZOS)
        card = Image.new('RGB', (1140, 790), 'white')
        x = (1140 - image.width) // 2
        y = 44 + (720 - image.height) // 2
        card.paste(image, (x, y))
        ImageDraw.Draw(card).text((18, 14), record['file'], fill='black')
        cards.append(card)
    sheet = Image.new('RGB', (2280, 3160), (235, 235, 235))
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % 2) * 1140, (index // 2) * 790))
    output = QA / 'Paper2_F1_F8_pdf_contact_sheet.png'
    sheet.save(output)
    return output


def main() -> None:
    pdfs = sorted(FIGURES.glob('F*.pdf'))
    if len(pdfs) != 8:
        raise RuntimeError(f'expected 8 PDF figures, found {len(pdfs)}')
    required = ['pdf', 'svg', 'eps', 'png']
    missing = [
        f'{path.stem}.{suffix}'
        for path in pdfs
        for suffix in required
        if not (FIGURES / f'{path.stem}.{suffix}').is_file()
    ]
    if missing:
        raise RuntimeError(f'missing figure exports: {missing}')
    records = [inspect_pdf(path) for path in pdfs]
    contact_sheet = make_contact_sheet(records)
    all_files = sorted(
        path for path in FIGURES.iterdir()
        if path.suffix.lower().lstrip('.') in required
    )
    manifest = [
        {'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha256(path)}
        for path in all_files
    ]
    report = {
        'status': 'PASS' if all(
            record['dimension_pass']
            and not record['spans_below_5p9_pt']
            and not record['out_of_page_text']
            and not record['type3_font_name_detected']
            for record in records
        ) else 'REVIEW_REQUIRED',
        'figure_count': len(records),
        'export_count': len(manifest),
        'records': records,
        'contact_sheet': contact_sheet.name,
        'manifest': manifest,
    }
    (QA / 'Paper2_FIGURE_QA.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    print(json.dumps({
        'status': report['status'],
        'figure_count': report['figure_count'],
        'export_count': report['export_count'],
        'minimum_text_sizes_pt': {
            record['file']: record['minimum_text_size_pt'] for record in records
        },
        'contact_sheet': str(contact_sheet),
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
