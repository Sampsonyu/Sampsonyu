"""Apply the profile's compact visual style without changing source statistics."""
from html import escape
import re
import xml.etree.ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def style_card(data, key):
    if key.startswith('pr-'):
        return data
    root = ET.fromstring(data)
    dark = key.endswith('-dark')
    accent = '#58a6ff' if dark else '#0969da'
    foreground = '#c9d1d9' if dark else '#57606a'
    if key.startswith('streak-'):
        return streak_card(root, dark)
    titles = {'timeline': 'Contribution timeline', 'stats': 'GitHub statistics',
              'languages': 'Languages by repository'}
    kind = key.rsplit('-', 1)[0]
    text_nodes = list(root.iter(f'{{{NS}}}text'))
    if not text_nodes:
        raise ValueError('Source card has no text')
    for index, node in enumerate(text_nodes):
        style = node.get('style', '')
        style = style.replace('#0366d6', accent).replace('#586069', foreground)
        if index == 0:
            node.text = titles[kind]
            style = re.sub(r'font-size:\s*22px', 'font-size: 16px; font-weight: 600', style)
        else:
            style = re.sub(r'font-size:\s*14px', 'font-size: 13px', style)
        node.set('style', style)
    return ET.tostring(root, encoding='utf-8')


def streak_card(root, dark):
    texts = [''.join(x.itertext()).strip() for x in root.iter(f'{{{NS}}}text')]
    if len(texts) != 9 or texts[1] != 'Total Contributions' or texts[3] != 'Current Streak' or texts[7] != 'Longest Streak':
        raise ValueError('Unexpected streak card structure; previous card will be retained')
    for value in [texts[0], texts[5], texts[6]]:
        if not re.fullmatch(r'[\d,]+', value):
            raise ValueError('Unexpected streak count')
    bg, border, fg, muted, accent = ('#0d1117', '#30363d', '#e6edf3', '#8b949e', '#58a6ff') if dark else ('#ffffff', '#d0d7de', '#1f2328', '#57606a', '#0969da')
    parts = [f'<svg xmlns="{NS}" width="700" height="112" viewBox="0 0 700 112" role="img" aria-label="Contribution streak statistics">',
             f'<rect x="0.5" y="0.5" width="699" height="111" rx="7" fill="{bg}" stroke="{border}"/>',
             '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" text-anchor="middle">']
    for x, label, value, date in [(117, 'Total contributions', texts[0], texts[2]), (350, 'Current streak', texts[5], texts[4]), (583, 'Longest streak', texts[6], texts[8])]:
        parts += [f'<text x="{x}" y="27" fill="{muted}" font-size="12">{label}</text>',
                  f'<text x="{x}" y="59" fill="{accent if x == 350 else fg}" font-size="23" font-weight="600">{escape(value)}</text>',
                  f'<text x="{x}" y="86" fill="{muted}" font-size="11">{escape(date)}</text>']
    parts += [f'<path d="M233 24v64M467 24v64" stroke="{border}"/>', '</g></svg>']
    return ''.join(parts).encode()
