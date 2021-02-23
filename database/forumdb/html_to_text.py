import lxml.html
from lxml.html.clean import Cleaner
from lxml.cssselect import CSSSelector


cleaner = Cleaner(
    scripts=True,
    javascript=True,
    comments=True,
    style=True,
    inline_style=True,
    links=True,
    meta=True,
    page_structure=True,
    processing_instructions=True,
    embedded=True,
    frames=True,
    forms=True,
    allow_tags=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'hr', 'li'],
    remove_unknown_tags=False,
    safe_attrs=[],
    safe_attrs_only=True,
)

blacklist_sel = CSSSelector(', '.join(
    [f'.block.{c}' for c in ['code', 'html', 'image', 'photo', 'video']]
    + ['.slide']
))


def clean_text(text: str) -> str:
    parts = [part.strip() for part in text.replace('\t', '').split('\n')]
    return ' '.join(part for part in parts if part)


def html_to_text(html: str) -> str:
    doc = lxml.html.fromstring(html)
    for kill_node in blacklist_sel(doc):
        kill_node.getparent().remove(kill_node)

    cleaner(doc)

    paragraphs = [clean_text(paragraph) for paragraph in doc.itertext()]
    return '\n'.join(paragraph for paragraph in paragraphs if paragraph)
