"""
Extract entities from the extracted POS tags.
"""

import csv
import datetime
import json
import os

names = set()
with open('pos_tags.txt', 'r') as file:
    data = file.read()
    for line_index, line in enumerate(data.split("\n")):
        try:
            parsed_line = json.loads(line)
        except Exception:
            continue
        parsed_line = [item if item is not None else '' for item in parsed_line]
        items = parsed_line[0].split('_')
        pos_tags = parsed_line[3].split('_')
        for item, pos_tag in zip(items, pos_tags):
            if pos_tag == 'SPEC(deeleigen)' and '-PER' in parsed_line[4]:
                names.add(item)
            elif '-LOC' in parsed_line[4]:
                names.add(item)

new_rows = []
names_found = set()
if os.path.exists('entity_mapping.csv'):
    with open('entity_mapping.csv', 'r') as file:
        rows = csv.reader(file)
        for row in rows:
            names_found.add(row[0])
            new_rows.append(row)

for name in names - names_found:
    new_rows.append([name, False, '', datetime.datetime.now()])

with open('entity_mapping.csv', 'w') as file:
    writer = csv.writer(file)
    for row in new_rows:
        writer.writerow(row)

