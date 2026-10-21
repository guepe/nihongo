#!/usr/bin/env python

"""
Import the lists/*.tsv files (kanji, kana, english, level[, french]) into
vocabulary/generated_<name>.toml. Words already in the library are skipped and
new ones are appended, so existing notes and their translations are kept.
"""

import csv
import glob
import os

from collections import OrderedDict

from library import INDEX_NAME
from library import NoteLibrary
from sort import write_toml

REPLACEMENTS = {
  '・する': 'する',
}

def correct_entry(entry: str) -> str:
  for match, replacement in REPLACEMENTS.items():
    if match in entry:
      entry = entry.replace(match, replacement)
  return entry

def hydrate_note(row):
  kanji = row[0]
  kana = row[1]
  english = row[2]
  level = row[3]

  keys = [
    ('kanji', kanji),
    ('kana', kana),
    ('english', english),
  ]
  # Optional fifth column: French translation.
  if len(row) > 4 and row[4].strip():
    keys.append(('french', row[4].strip()))
  keys.extend([
    ('source', 'wiktionary'),
    ('level', level),
    ('tags', ['generated', 'tsv']),
  ])
  return OrderedDict(keys)

def tsv_to_toml_filename(filename):
  path = os.path.splitext(filename)[0]
  base = os.path.basename(path)
  return 'vocabulary/generated_{}.toml'.format(base)

def main():
  # Load existing library
  note_library = NoteLibrary()
  note_library.load_library()

  # Scan and convert the tsv files
  for filename in glob.glob('lists/*.tsv', recursive=True):
    if 'n4' in filename:
      continue
    notes = []
    with open(filename) as fd:
      rd = csv.reader(fd, delimiter='\t', quotechar='"')
      for row in rd:
        kanji = row[0] = correct_entry(row[0])
        kana = row[1] = correct_entry(row[1])
        if kanji in note_library.notes or kana in note_library.notes:
          continue
        note = hydrate_note(row)
        notes.append(note)

    new_filename = tsv_to_toml_filename(filename)
    if not notes:
      print('No new notes in {}'.format(filename))
      continue

    # NB: Append, never overwrite: the existing notes may have been edited/translated.
    toml = {INDEX_NAME: []}
    if os.path.exists(new_filename):
      toml = NoteLibrary.read_notes_from_toml_file(new_filename)
    toml[INDEX_NAME].extend(notes)

    print('Adding {} notes to {}'.format(len(notes), new_filename))
    write_toml(toml, new_filename)
    note_library.add_notes_from_file(new_filename)

if __name__ == '__main__':
    main()

