"""Combine public SVG cards into a single, self-contained black profile panel."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import re
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'profile'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
URLS = {
    'languages': 'https://github-readme-stats.vercel.app/api/top-langs/?username=dryhour&layout=compact&hide=css,html,scss&langs_count=8&hide_border=true&theme=tokyonight&bg_color=000000&title_color=8957e5&border_radius=0&card_width=300&disable_animations=true',
    'stats': 'https://github-readme-stats.vercel.app/api?username=dryhour&show_icons=true&hide_border=true&theme=tokyonight&bg_color=000000&title_color=8957e5&icon_color=1f6feb&border_radius=0&custom_title=GitHub%20Stats&disable_animations=true',
    'streak': 'https://streak-stats.demolab.com?user=dryhour&theme=tokyonight&hide_border=true&background=000000&border_radius=0&ring=8957e5&fire=1f6feb&currStreakLabel=8957e5',
    'followers': 'https://img.shields.io/github/followers/dryhour?style=for-the-badge&logo=github&color=1f6feb&labelColor=000000',
}


def validate(raw):
    node = ET.fromstring(raw)
    if node.tag != f'{{{NS}}}svg':
        raise ValueError('Response is not an SVG')
    visible = ' '.join(node.itertext()).lower()
    for error in ('something went wrong', 'rate limit', 'user not found', 'could not fetch', 'is invalid', 'invalid query', 'service unavailable'):
        if error in visible:
            raise ValueError('Provider returned an error card: ' + error)
    for child in node.iter():
        if child.tag.split('}')[-1] in ('script', 'foreignObject'):
            raise ValueError('Expected self-contained vector artwork')
        if child.tag.split('}')[-1] == 'image':
            href = child.get('href', child.get('{http://www.w3.org/1999/xlink}href', ''))
            if not href.startswith('data:image/'):
                raise ValueError('External image reference is not self-contained')
    return node


def fetch(item):
    name, url = item
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = urllib.request.urlopen(request, timeout=35).read()
    validate(data)
    return name, data


def card(name):
    node = validate((ASSETS / (name + '.svg')).read_bytes())
    ids = {c.get('id') for c in node.iter() if c.get('id')}
    classes = {v for c in node.iter() for v in c.get('class', '').split()}
    for child in node.iter():
        if child.get('id'):
            child.set('id', name + '-' + child.get('id'))
        if child.get('class'):
            child.set('class', ' '.join(name + '-' + v for v in child.get('class').split()))
        for key, value in list(child.attrib.items()):
            if key == 'style' and 'animation:' in value:
                value = re.sub(r'animation\s*:[^;]+;?', '', value)
                value = re.sub(r'opacity\s*:\s*0\s*(?=;|$)', 'opacity: 1', value)
            for ident in ids:
                value = value.replace('url(#' + ident + ')', 'url(#' + name + '-' + ident + ')')
                if value == '#' + ident:
                    value = '#' + name + '-' + ident
            if key in ('aria-labelledby', 'aria-describedby'):
                value = ' '.join(name + '-' + v if v in ids else v for v in value.split())
            child.set(key, value)
        if child.tag == f'{{{NS}}}style' and child.text:
            css = child.text
            for cls in sorted(classes, key=len, reverse=True):
                css = re.sub(r'\.' + re.escape(cls) + r'(?![\w-])', '.' + name + '-' + cls, css)
            for ident in ids:
                css = css.replace('url(#' + ident + ')', 'url(#' + name + '-' + ident + ')')
            animations = re.findall(r'@keyframes\s+([\w-]+)', css)
            for animation in animations:
                css = re.sub(r'\b' + re.escape(animation) + r'\b', name + '-' + animation, css)
            child.text = css
    return node


def size(node):
    box = node.get('viewBox')
    if box:
        return tuple(map(float, box.split()[-2:]))
    return float(node.get('width')), float(node.get('height'))


def build():
    panel = ET.Element(f'{{{NS}}}svg', {'width': '1340', 'height': '400', 'viewBox': '0 0 1340 400', 'role': 'img', 'aria-labelledby': 'panel-title panel-desc'})
    ET.SubElement(panel, f'{{{NS}}}title', {'id': 'panel-title'}).text = 'dryhour — Quantitative Finance, Data Analytics, Software Engineering'
    ET.SubElement(panel, f'{{{NS}}}desc', {'id': 'panel-desc'}).text = 'GitHub languages, activity, contribution streak, and followers on a solid black background.'
    ET.SubElement(panel, f'{{{NS}}}rect', {'width': '1340', 'height': '400', 'fill': '#000000'})
    ET.SubElement(panel, f'{{{NS}}}text', {'x': '670', 'y': '81', 'text-anchor': 'middle', 'fill': '#ffffff', 'font-family': 'Arial, Helvetica, sans-serif', 'font-weight': '700', 'font-size': '52'}).text = 'QUANT - DATA - SWE'
    # Preserve each original card's aspect ratio and give all three equal height.
    cards = [card(name) for name in ('languages', 'stats', 'streak')]
    widths = [size(c)[0] * 190 / size(c)[1] for c in cards]
    gap = 10
    x = (1340 - sum(widths) - gap * 2) / 2
    for node, width in zip(cards, widths):
        node.set('x', str(x))
        node.set('y', '133')
        node.set('width', str(width))
        node.set('height', '190')
        panel.append(node)
        x += width + gap
    follower = card('followers')
    fw, fh = size(follower)
    follower.set('x', str((1340 - fw) / 2))
    follower.set('y', '351')
    panel.append(follower)
    # Rendering must work inside an <img>, without external resources or JS.
    ET.SubElement(panel, f'{{{NS}}}style').text = '* { animation-duration: 0s !important; animation-delay: 0s !important; }'
    out = ET.tostring(panel, encoding='unicode')
    (ROOT / 'profile.svg').write_text(out, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cached', action='store_true', help='Build using saved cards without network requests')
    args = parser.parse_args()
    ASSETS.mkdir(parents=True, exist_ok=True)
    if not args.cached:
        # Fetch and validate every card before replacing any previous good artwork.
        # A provider outage fails the job, leaving the committed panel intact.
        with ThreadPoolExecutor(max_workers=4) as pool:
            fetched = list(pool.map(fetch, URLS.items()))
        for name, data in fetched:
            (ASSETS / (name + '.svg')).write_bytes(data)
    build()
    print('Built profile.svg')


if __name__ == '__main__':
    main()
