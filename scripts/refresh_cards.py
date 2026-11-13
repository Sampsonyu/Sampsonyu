"""Refresh public SVG cards; keep the last valid file if a service fails."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import json
import xml.etree.ElementTree as ET
from style_cards import style_card

ROOT = Path(__file__).resolve().parents[1]


def validate_svg(data):
    svg = ET.fromstring(data)
    if svg.tag != '{http://www.w3.org/2000/svg}svg':
        raise ValueError('Response is not an SVG')
    visible = ' '.join(svg.itertext()).lower()
    for failure in ['something went wrong', 'rate limit', 'invalid user',
                    'user not found', 'could not fetch', 'upstream error',
                    'inaccessible', 'invalid query', 'bad credentials',
                    'no result', 'application error', 'service unavailable']:
        if failure in visible:
            raise ValueError('Service returned an error card: ' + failure)
    if any(x.tag.rsplit('}', 1)[-1] in ('script', 'foreignObject') for x in svg.iter()):
        raise ValueError('Unexpected active SVG content')


def main():
    cards = json.loads((ROOT / 'scripts/cards.json').read_text())
    metadata_path = ROOT / 'assets/updated.json'
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    failures = 0
    for key, url in cards.items():
        try:
            req = Request(url, headers={'User-Agent': 'GitHub-Profile-Card-Refresh'})
            with urlopen(req, timeout=40) as response:
                data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError('Card response exceeds size limit')
            validate_svg(data)
            data = style_card(data, key)
            validate_svg(data)
            target = ROOT / 'assets' / (key + '.svg')
            temporary = target.with_suffix('.svg.tmp')
            temporary.write_bytes(data)
            temporary.replace(target)
            metadata[key] = {'last_success_utc': datetime.now(timezone.utc).isoformat(), 'source': url}
            print('Updated ' + key)
        except Exception as exc:
            failures += 1
            print(f'::warning::Kept previous {key}: {exc}')
    metadata_path.write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'{len(cards) - failures}/{len(cards)} cards refreshed.')
    if failures == len(cards):
        raise SystemExit('All card services failed; previous assets were preserved.')


if __name__ == '__main__':
    main()
