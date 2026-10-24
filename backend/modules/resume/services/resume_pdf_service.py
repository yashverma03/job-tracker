import io
import os
import re
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from common.exceptions.api_exceptions import ApiError
from modules.resume.types.resume_types import ResumeContent, ResumeInput

PAGE_MARGIN = 0.45 * inch

# Metric-compatible open-source substitutes for the requested proprietary fonts.
pdfmetrics.registerFont(TTFont('Cambria', '/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Cambria-Bold', '/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Calibri', '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Calibri-Bold', '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Calibri-Italic', '/usr/share/fonts/truetype/crosextra/Carlito-Italic.ttf'))
pdfmetrics.registerFont(TTFont('TimesNewRoman', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'))
pdfmetrics.registerFontFamily('Cambria', normal='Cambria', bold='Cambria-Bold')
pdfmetrics.registerFontFamily('Calibri', normal='Calibri', bold='Calibri-Bold', italic='Calibri-Italic')
pdfmetrics.registerFontFamily('TimesNewRoman', normal='TimesNewRoman', bold='TimesNewRoman-Bold')

NAME_STYLE = ParagraphStyle('Name', fontName='TimesNewRoman-Bold', fontSize=16, alignment=1, spaceAfter=14)
CONTACT_STYLE = ParagraphStyle('Contact', fontName='Calibri', fontSize=9, alignment=1, textColor=colors.HexColor('#333333'))
HEADING_STYLE = ParagraphStyle('Heading', fontName='Cambria-Bold', fontSize=12, spaceBefore=22, spaceAfter=6)
BODY_STYLE = ParagraphStyle('Body', fontName='Calibri', fontSize=11, leading=13)
BULLET_STYLE = ParagraphStyle(
    'Bullet', fontName='Calibri', fontSize=11, leading=13,
    leftIndent=16, bulletIndent=2, bulletFontName='Calibri', spaceAfter=2,
)
ROLE_STYLE = ParagraphStyle('Role', fontName='Calibri-Bold', fontSize=11)
DATE_STYLE = ParagraphStyle('Date', fontName='Calibri-Italic', fontSize=10, alignment=2, textColor=colors.HexColor('#333333'))


def _link(url: str, label: str) -> str:
    return f'<link href="{url}"><font color="#1a56db"><u>{label}</u></font></link>'


def _render_bullet(text: str) -> str:
    # Stored bullets mark metrics with **double asterisks**; escape any raw XML-special characters first
    # (Paragraph markup is HTML-like) so the metric markers are the only thing translated into <b> tags.
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escape(text))


def _heading(text: str) -> list:
    return [
        Paragraph(text, HEADING_STYLE),
        HRFlowable(width='100%', thickness=0.75, color=colors.HexColor('#999999'), spaceAfter=4),
    ]


def _two_column_row(left: str, right: str, left_style: ParagraphStyle, right_style: ParagraphStyle, usable_width: float) -> Table:
    table = Table(
        [[Paragraph(left, left_style), Paragraph(right, right_style)]],
        colWidths=[usable_width * 0.7, usable_width * 0.3],
    )
    table.hAlign = 'LEFT'
    table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return table


def _build_story(resume_input: ResumeInput, content: ResumeContent, usable_width: float) -> list:
    contact = resume_input.contact
    contact_line = ' | '.join([
        _link(contact.portfolio_url, 'Portfolio'),
        contact.email,
        contact.phone,
        _link(contact.linkedin_url, 'LinkedIn'),
        _link(contact.github_url, 'GitHub'),
        _link(contact.gfg_url, 'GFG'),
        _link(contact.leetcode_url, 'LeetCode'),
    ])
    story = [
        Paragraph(contact.name, NAME_STYLE),
        Paragraph(contact_line, CONTACT_STYLE),
        Spacer(1, 12),
    ]

    story += _heading('SUMMARY')
    story.append(Paragraph(content.summary, BODY_STYLE))

    story += _heading('EXPERIENCE')
    experience_entries = list(zip(resume_input.experience, content.experience_bullets))
    for i, (entry, bullets) in enumerate(experience_entries):
        story.append(_two_column_row(
            f'{entry.title} | {entry.company}', entry.duration, ROLE_STYLE, DATE_STYLE, usable_width,
        ))
        story.append(Spacer(1, 3))
        for bullet in bullets:
            story.append(Paragraph(_render_bullet(bullet), BULLET_STYLE, bulletText='●'))
        if i < len(experience_entries) - 1:
            story.append(Spacer(1, 14))

    story += _heading('SKILLS')
    if content.skills:
        story.append(Paragraph(', '.join(content.skills), BULLET_STYLE, bulletText='●'))

    story += _heading('CERTIFICATIONS')
    for cert in resume_input.certifications:
        story.append(Paragraph(_link(cert.url, cert.label), BULLET_STYLE, bulletText='●'))

    story += _heading('EDUCATION')
    for edu in resume_input.education:
        story.append(_two_column_row(
            f'{edu.degree}, {edu.institution}', edu.years, BODY_STYLE, DATE_STYLE, usable_width,
        ))

    return story


def render_resume_pdf(resume_input: ResumeInput, content: ResumeContent, output_path: str) -> None:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        title=f'{resume_input.contact.name} Resume',
        author=resume_input.contact.name,
    )
    # SimpleDocTemplate's default Frame adds 6pt of padding on each side beyond leftMargin/rightMargin;
    # Paragraphs wrap within that inset automatically, so our manual Table widths must match it too.
    usable_width = A4[0] - PAGE_MARGIN * 2 - 12

    story = _build_story(resume_input, content, usable_width)
    doc.build(story)

    page_count = len(PdfReader(io.BytesIO(buffer.getvalue())).pages)
    if page_count > 1:
        raise ApiError(
            f'Generated resume would span {page_count} pages; content must fit on a single page.',
            status_code=500,
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())
