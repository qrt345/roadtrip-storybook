"""Offline, data-driven travel deck builder. Python 3.9+, standard library only."""
import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
STATUSES = {'confirmed', 'booked', 'planned', 'pending', 'reference'}
ICONS = {'house', 'tower', 'mountain', 'tree', 'fish', 'cup', 'charge', 'flag', 'hotpot', 'bag', 'sun'}
MODES = {'car', 'walk', 'cable', 'train', 'boat'}


def require(condition, path, reason):
    if not condition:
        raise ValueError(f'{path}: {reason}')


def fields(obj, path, allowed, required=()):
    require(isinstance(obj, dict), path, 'expected an object')
    unknown = set(obj) - set(allowed)
    require(not unknown, path, f'unknown fields: {sorted(unknown)}')
    for key in required:
        require(key in obj, path, f'missing {key}')


def text(value, path, nonempty=False):
    require(isinstance(value, str), path, 'expected plain text')
    require(not nonempty or bool(value.strip()), path, 'must not be empty')


def optional_text(obj, path, names):
    for name in names:
        if name in obj:
            text(obj[name], path + '.' + name)


def boolean(obj, key, path):
    if key in obj:
        require(type(obj[key]) is bool, path + '.' + key, 'expected true or false')


def items(value, path, nonempty=False):
    require(isinstance(value, list), path, 'expected an array')
    require(not nonempty or len(value) > 0, path, 'must not be empty')
    return enumerate(value)


def identifier(value, path):
    require(isinstance(value, str) and bool(SLUG.fullmatch(value)), path, 'use lowercase letters, digits and hyphens')


def unique_ids(values, path):
    found = set()
    for i, value in items(values, path):
        require(isinstance(value, dict) and 'id' in value, f'{path}[{i}]', 'missing id')
        identifier(value['id'], f'{path}[{i}].id')
        require(value['id'] not in found, path, 'duplicate id ' + value['id'])
        found.add(value['id'])
    return found


def sections(value, path):
    for i, section in items(value, path):
        pos = f'{path}[{i}]'
        fields(section, pos, {'title', 'time', 'body', 'status'}, {'title'})
        text(section['title'], pos + '.title', True)
        optional_text(section, pos, ['time', 'body'])
        if 'status' in section:
            require(section['status'] in STATUSES, pos, 'invalid status')


def validate_map(value, path, pages):
    fields(value, path, {'title', 'finish', 'nodes', 'legs'}, {'nodes'})
    optional_text(value, path, ['title', 'finish'])
    items(value['nodes'], path + '.nodes', True)
    node_ids = unique_ids(value['nodes'], path + '.nodes')
    for i, node in enumerate(value['nodes']):
        pos = f'{path}.nodes[{i}]'
        fields(node, pos, {'id', 'label', 'detail', 'icon', 'page', 'x', 'y', 'dx', 'dy'}, {'id', 'label'})
        text(node['label'], pos + '.label', True)
        optional_text(node, pos, ['detail'])
        if 'icon' in node:
            require(node['icon'] in ICONS, pos, 'unknown icon')
        if 'page' in node:
            require(node['page'] in pages, pos, 'unknown target page')
        require(('x' in node) == ('y' in node), pos, 'x and y must appear together')
        if len(node_ids) > 8:
            require('x' in node, pos, 'more than 8 nodes require coordinates; consider splitting the page')
        for key, low, high in [('x', 60, 660), ('y', 100, 540), ('dx', -180, 180), ('dy', -130, 100)]:
            if key in node:
                n = node[key]
                require(type(n) in (int, float) and math.isfinite(n) and low <= n <= high, pos + '.' + key, f'expected number between {low} and {high}')
    for i, leg in items(value.get('legs', []), path + '.legs'):
        pos = f'{path}.legs[{i}]'
        fields(leg, pos, {'from', 'to', 'mode', 'label', 'optional'}, {'from', 'to'})
        require(leg['from'] in node_ids and leg['to'] in node_ids, pos, 'unknown route node')
        require(leg['from'] != leg['to'], pos, 'a route segment must connect different nodes')
        require(leg.get('mode', 'car') in MODES, pos, 'unknown transport mode')
        optional_text(leg, pos, ['label'])
        boolean(leg, 'optional', pos)


def validate(data):
    fields(data, 'trip', {'version', 'id', 'title', 'brand', 'edition', 'snapshot', 'source_md', 'source_note', 'theme', 'pages'}, {'version', 'id', 'title', 'pages'})
    require(type(data['version']) is int and data['version'] == 1, 'version', 'only version 1 is supported')
    identifier(data['id'], 'id')
    text(data['title'], 'title', True)
    optional_text(data, 'trip', ['brand', 'edition', 'snapshot', 'source_md', 'source_note'])
    theme = data.get('theme', {})
    fields(theme, 'theme', {'accent', 'ink', 'paper', 'map'})
    for key, color in theme.items():
        require(isinstance(color, str) and bool(re.fullmatch(r'#[0-9a-fA-F]{6}', color)), 'theme.' + key, 'expected #RRGGBB')
    items(data['pages'], 'pages', True)
    page_ids = unique_ids(data['pages'], 'pages')
    for i, page in enumerate(data['pages']):
        pos = f'pages[{i}]'
        fields(page, pos, {'id', 'name', 'chapter', 'eyebrow', 'title', 'accent_line', 'lead', 'foot', 'cover', 'metrics', 'companions', 'sections', 'note', 'warning', 'table', 'checklist', 'choices', 'map'}, {'id', 'name', 'title', 'map'})
        text(page['name'], pos + '.name', True)
        optional_text(page, pos, ['chapter', 'eyebrow', 'lead', 'foot', 'note'])
        boolean(page, 'cover', pos)
        boolean(page, 'warning', pos)
        titles = [page['title']] if isinstance(page['title'], str) else page['title']
        for j, line in items(titles, pos + '.title', True):
            text(line, f'{pos}.title[{j}]', True)
        require(len(titles) <= 3, pos + '.title', 'use at most 3 title lines')
        if 'accent_line' in page:
            require(type(page['accent_line']) is int and 0 <= page['accent_line'] < len(titles), pos, 'accent_line out of range')
        for j, metric in items(page.get('metrics', []), pos + '.metrics'):
            fields(metric, pos + '.metrics', {'value', 'unit', 'label'}, {'value'})
            optional_text(metric, pos + f'.metrics[{j}]', ['value', 'unit', 'label'])
        for j, person in items(page.get('companions', []), pos + '.companions'):
            fields(person, pos + '.companions', {'label', 'icon'}, {'label'})
            text(person['label'], pos + '.companions.label')
            require(person.get('icon', 'person') in {'dog', 'person', 'bag', 'bichon', 'poodle', 'dachshund', 'corgi'}, pos, 'unknown companion icon')
        sections(page.get('sections', []), pos + '.sections')
        if 'table' in page:
            table = page['table']
            fields(table, pos + '.table', {'headers', 'rows'}, {'headers', 'rows'})
            for j, heading in items(table['headers'], pos + '.table.headers', True):
                text(heading, pos + f'.table.headers[{j}]')
            for j, row in items(table['rows'], pos + '.table.rows'):
                items(row, pos + f'.table.rows[{j}]')
                require(len(row) == len(table['headers']), pos + '.table', 'table row width differs from headers')
                for cell in row:
                    text(cell, pos + '.table.cell')
        unique_ids(page.get('checklist', []), pos + '.checklist')
        for item in page.get('checklist', []):
            fields(item, pos + '.checklist', {'id', 'label'}, {'id', 'label'})
            text(item['label'], pos + '.checklist.label', True)
        unique_ids(page.get('choices', []), pos + '.choices')
        for j, choice in enumerate(page.get('choices', [])):
            cp = pos + f'.choices[{j}]'
            fields(choice, cp, {'id', 'label', 'sections', 'note', 'map'}, {'id', 'label'})
            text(choice['label'], cp + '.label', True)
            optional_text(choice, cp, ['note'])
            sections(choice.get('sections', []), cp + '.sections')
            if 'map' in choice:
                validate_map(choice['map'], cp + '.map', page_ids)
        validate_map(page['map'], pos + '.map', page_ids)
    return data


def inline(value):
    value = html.escape(value)
    # Only explicit web links; local paths remain plain text in the shareable snapshot.
    value = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', lambda m: '<a href="' + m[2] + '" target="_blank" rel="noopener">' + m[1] + '</a>', value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', value)
    return value


def markdown(source):
    lines = source.splitlines(); out = []; i = 0
    while i < len(lines):
        line = lines[i].strip(); i += 1
        if not line:
            continue
        if line.startswith('|'):
            raw = [line]
            while i < len(lines) and lines[i].strip().startswith('|'):
                raw.append(lines[i].strip()); i += 1
            rows = [[x.strip() for x in row.strip('|').split('|')] for row in raw]
            rows = [row for row in rows if not all(re.fullmatch(r':?-+:?', x) for x in row)]
            if rows:
                head = ''.join('<th>' + inline(x) + '</th>' for x in rows[0])
                body = ''.join('<tr>' + ''.join('<td>' + inline(x) + '</td>' for x in row) + '</tr>' for row in rows[1:])
                out.append('<div class="source-table-wrap"><table><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table></div>')
            continue
        heading = re.match(r'^(#{1,6}) (.+)', line)
        if heading:
            n = len(heading[1]); out.append(f'<h{n}>' + inline(heading[2]) + f'</h{n}>'); continue
        if line.startswith('> '):
            out.append('<blockquote>' + inline(line[2:]) + '</blockquote>'); continue
        if re.match(r'^(- |\d+\. )', line):
            tag = 'ul' if line.startswith('- ') else 'ol'
            pattern = r'^- ' if tag == 'ul' else r'^\d+\. '
            values = [re.sub(pattern, '', line)]
            while i < len(lines) and re.match(pattern, lines[i].strip()):
                values.append(re.sub(pattern, '', lines[i].strip())); i += 1
            out.append('<' + tag + '>' + ''.join('<li>' + inline(x.replace('[ ] ', '□ ', 1)) + '</li>' for x in values) + '</' + tag + '>'); continue
        out.append('<p>' + inline(line) + '</p>')
    return '\n'.join(out)


def load(source):
    data = validate(json.loads(source.read_text(encoding='utf-8-sig')))
    content = ''; source_path = None
    if data.get('source_md'):
        relative = Path(data['source_md'])
        require(not relative.is_absolute(), 'source_md', 'must be relative to input directory')
        source_path = (source.parent / relative).resolve()
        require(source.parent.resolve() in source_path.parents, 'source_md', 'must stay within input directory')
        require(source_path.suffix.lower() == '.md' and source_path.is_file(), 'source_md', 'expected an existing Markdown file')
        content = source_path.read_text(encoding='utf-8-sig')
    return data, content, source_path


def render(data, source):
    theme = data.get('theme', {})
    overrides = ':root{' + ''.join('--' + ('orange' if k == 'accent' else k) + ':' + v + ';' for k, v in theme.items()) + '}'
    source_note = '\n'.join(x for x in [data.get('snapshot', ''), data.get('source_note', '')] if x) or '以下内容按提供的行程资料整理。'
    encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    replacements = {
        '__TITLE__': html.escape(data['title']), '__BRAND__': html.escape(data.get('brand', '一路有你')),
        '__EDITION__': html.escape(data.get('edition', '旅行手账')), '__PAPER__': theme.get('paper', '#f6f1e5'),
        '__SOURCE_HASH__': hashlib.sha256(source.encode('utf-8')).hexdigest() if source else '',
        '__SOURCE_NOTE__': html.escape(source_note).replace('\n', '<br>'),
        '__SOURCE_HTML__': markdown(source) if source else '<p>本手账未附加独立原文；请按各页的来源和确认状态查看安排。</p>',
        '__DATA__': encoded,
        '__SPECTRUM_LICENSE__': html.escape((ASSETS / 'vendor/SPECTRUM-LICENSE.txt').read_text(encoding='utf-8')),
        '/*__CSS__*/': (ASSETS / 'deck.css').read_text(encoding='utf-8') + overrides,
        '/*__APP__*/': (ASSETS / 'deck.js').read_text(encoding='utf-8'),
        '/*__ILLUSTRATIONS__*/': (ASSETS / 'illustrations.js').read_text(encoding='utf-8'),
        '/*__GSAP__*/': (ASSETS / 'vendor/gsap.min.js').read_text(encoding='utf-8'),
        '/*__MOTIONPATH__*/': (ASSETS / 'vendor/MotionPathPlugin.min.js').read_text(encoding='utf-8'),
    }
    template = (ASSETS / 'deck.html').read_text(encoding='utf-8')
    # One substitution pass: input text that resembles a template marker stays literal.
    matcher = re.compile('|'.join(re.escape(k) for k in replacements))
    return matcher.sub(lambda match: replacements[match[0]], template)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', type=Path); group.add_argument('--batch', type=Path)
    parser.add_argument('--output', type=Path); parser.add_argument('--out-dir', type=Path)
    parser.add_argument('--force', action='store_true'); parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        require(not args.input or not args.out_dir, 'arguments', '--out-dir is for --batch')
        require(not args.batch or not args.output, 'arguments', '--output is for --input')
        inputs = [args.input.resolve()] if args.input else sorted(args.batch.resolve().glob('*.json'))
        require(bool(inputs), 'batch', 'no JSON files found')
        if not args.check:
            require(bool(args.output if args.input else args.out_dir), 'arguments', 'supply --output or --out-dir')
        jobs = []; seen_ids = set(); seen_outputs = set(); protected = set(inputs)
        for path in inputs:
            try:
                data, content, source_path = load(path)
            except (ValueError, TypeError, KeyError, OSError) as error:
                raise ValueError(f'{path.name}: {error}') from error
            require(data['id'] not in seen_ids, path.name, 'duplicate trip id in batch')
            seen_ids.add(data['id'])
            if source_path:
                protected.add(source_path)
            if args.check:
                continue
            output = args.output.resolve() if args.input else (args.out_dir / (path.stem + '.html')).resolve()
            require(output.suffix.lower() == '.html', str(output), 'output must end in .html')
            key = str(output).casefold()
            require(key not in seen_outputs, str(output), 'duplicate output path')
            require(not output.exists() or (args.force and output.is_file()), str(output), 'output exists; use --force for an authorized update')
            seen_outputs.add(key)
            jobs.append((output, render(data, content), len(data['pages'])))
        require(not any(output in protected for output, _, _ in jobs), 'output', 'would overwrite an input or source file')
        generated = []
        for output, document, pages in jobs:
            output.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(prefix='.trip-', suffix='.tmp', dir=output.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as file:
                    file.write(document)
                if args.force:
                    os.replace(temp_name, output)
                else:
                    # Exclusive creation protects against another process writing after preflight.
                    with output.open('xb') as file:
                        file.write(Path(temp_name).read_bytes())
                generated.append({'file': str(output), 'pages': pages})
            finally:
                Path(temp_name).unlink(missing_ok=True)
        print(json.dumps({'validated': len(inputs), 'generated': generated, 'check_only': args.check}, ensure_ascii=True))
        return 0
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
