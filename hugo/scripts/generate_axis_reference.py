#!/usr/bin/env python3
"""Render both axis YAML lookup pages from the shared reference source.

Run with --check in CI to detect stale generated Markdown. Standard library only.
"""
import argparse
import json
from pathlib import Path

HUGO = Path(__file__).resolve().parents[1]
BEGIN = '<!-- BEGIN GENERATED AXIS YAML REFERENCE -->'
END = '<!-- END GENERATED AXIS YAML REFERENCE -->'


def render(sections):
    table = ['| Key | Description | Requirement |', '| --- | --- | --- |']
    headings = []
    seen = set()
    for section in sections:
        headings.extend(['## ' + section['name'], ''])
        for group in section['groups']:
            label = ' / '.join('`' + key + '`' for key in group['keys'])
            requirement = group['requirement']
            headings.append('- ' + label + ' (' + requirement + ') — ' + group['description'])
            for entry in group['entries']:
                key = entry['key']
                if key in seen:
                    raise ValueError('Duplicate reference key: ' + key)
                seen.add(key)
                table.append('| `' + key + '` | ' + (entry['summary'] or group['description']) + ' | ' + requirement + ' |')
        headings.append('')
    return {'axisYamlSettingsTable.md': '\n'.join(table),
            'axisYamlSettingsHeadings.md': '\n'.join(headings).rstrip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    source = json.loads((HUGO / 'reference/axis-yaml-settings.json').read_text())
    stale = []
    for name, body in render(source['sections']).items():
        path = HUGO / 'content/manual/motion_cfg' / name
        current = path.read_text()
        before, rest = current.split(BEGIN, 1)
        _, after = rest.split(END, 1)
        expected = before + BEGIN + '\n\n' + body + '\n\n' + END + after
        if expected != current:
            stale.append(str(path.relative_to(HUGO)))
            if not args.check:
                path.write_text(expected)
    if args.check and stale:
        parser.exit(1, 'Stale axis reference pages; run python3 hugo/scripts/generate_axis_reference.py:\n' + '\n'.join(stale) + '\n')
    print('Axis YAML reference pages are current.' if args.check else 'Generated both axis YAML reference pages.')


if __name__ == '__main__':
    main()
