#!/usr/bin/env python

"""
Track and manage the French translation of the vocabulary.

  python cardgen/translation_status.py                      # progress report
  python cardgen/translation_status.py --missing --level n5 # untranslated notes
  python cardgen/translation_status.py --export n5.tsv --level n5
  python cardgen/translation_status.py --import n5.tsv

Exported TSV files can be filled in with a spreadsheet or an LLM (fill the
'french' column only), then imported back. Notes are matched on kanji + kana +
english, so the same word with two different meanings is handled separately.
"""

import argparse
import csv
import glob
import sys
from collections import OrderedDict

from library import INDEX_NAME
from library import NoteLibrary
from library import write_toml

FRENCH_FIELD = 'french'
TSV_COLUMNS = ['kanji', 'kana', 'level', 'english', 'french', 'file']
NO_LEVEL = '-'

def vocabulary_files():
  # NB: Same selection as generate_vocabulary_deck.py
  for filename in sorted(glob.glob('**/*.toml', recursive=True)):
    if 'cardgen' in filename or 'temp/' in filename:
      continue
    yield filename

def is_translated(note):
  return bool(note.get(FRENCH_FIELD, '').strip())

def note_key(note):
  return (note['kanji'], note['kana'], note['english'])

def load_notes():
  """Yield (filename, note) for every active note."""
  for filename in vocabulary_files():
    for note in NoteLibrary.read_notes_from_toml_file(filename)[INDEX_NAME]:
      if note.get('disabled'):
        continue
      yield filename, note

def matches_level(note, level):
  return not level or note.get('level', NO_LEVEL) == level

def print_report():
  by_file = OrderedDict()
  by_level = {}
  for filename, note in load_notes():
    for stats, key in ((by_file, filename), (by_level, note.get('level', NO_LEVEL))):
      done, total = stats.get(key, (0, 0))
      stats[key] = (done + is_translated(note), total + 1)

  def print_table(title, stats):
    print('==== {0} ===='.format(title))
    for key, (done, total) in stats.items():
      print('{0: <50} {1: >5} / {2: <5} {3: >4.0%}'.format(key, done, total, done / total))

  print_table('Par fichier', by_file)
  print_table('Par niveau', OrderedDict(sorted(by_level.items())))
  done = sum(d for d, _ in by_file.values())
  total = sum(t for _, t in by_file.values())
  print('==== Total : {0} / {1} ({2:.1%}) ===='.format(done, total, done / total))

def missing_notes(level, limit):
  seen = set()
  rows = []
  for filename, note in load_notes():
    if is_translated(note) or not matches_level(note, level) or note_key(note) in seen:
      continue
    seen.add(note_key(note))
    rows.append((filename, note))
    if limit and len(rows) >= limit:
      break
  return rows

def print_missing(level, limit):
  for filename, note in missing_notes(level, limit):
    print('{0}\t{1}\t{2}\t{3}'.format(note['kanji'], note['kana'], note['english'], filename))

def export_tsv(filename, level, limit, include_translated):
  seen = set()
  count = 0
  with open(filename, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter='\t', lineterminator='\n')
    writer.writerow(TSV_COLUMNS)
    for source, note in load_notes():
      if not include_translated and is_translated(note):
        continue
      if not matches_level(note, level) or note_key(note) in seen:
        continue
      seen.add(note_key(note))
      writer.writerow([note['kanji'], note['kana'], note.get('level', ''),
          note['english'], note.get(FRENCH_FIELD, ''), source])
      count += 1
      if limit and count >= limit:
        break
  print('Exported {0} notes to {1}'.format(count, filename))

def read_translations(filename):
  translations = {}
  with open(filename, 'r', encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f, delimiter='\t'):
      french = ' '.join((row.get('french') or '').split()) # No tabs or newlines.
      if french:
        translations[(row['kanji'], row['kana'], row['english'])] = french
  return translations

def with_french(note, french):
  """Return a copy of the note with the French placed right after the English."""
  updated = OrderedDict()
  for key, value in note.items():
    if key == FRENCH_FIELD:
      continue
    updated[key] = value
    if key == 'english':
      updated[FRENCH_FIELD] = french
  return updated

def import_tsv(filename):
  translations = read_translations(filename)
  matched = set()
  updated_count = 0
  unchanged_count = 0

  for source in vocabulary_files():
    data = NoteLibrary.read_notes_from_toml_file(source)
    changed = False
    for i, note in enumerate(data[INDEX_NAME]):
      key = note_key(note)
      if key not in translations:
        continue
      matched.add(key)
      if note.get(FRENCH_FIELD) == translations[key]:
        unchanged_count += 1
        continue
      data[INDEX_NAME][i] = with_french(note, translations[key])
      changed = True
      updated_count += 1
    if changed:
      write_toml(data, source)
      print('Updated: {0}'.format(source))

  print('Translations in file: {0}'.format(len(translations)))
  print('  > notes updated: {0}'.format(updated_count))
  print('  > already up to date: {0}'.format(unchanged_count))
  not_found = [k for k in translations if k not in matched]
  if not_found:
    print('  > NOT FOUND (kanji/kana/english changed?): {0}'.format(len(not_found)))
    for kanji, kana, english in not_found:
      print('      {0}\t{1}\t{2}'.format(kanji, kana, english))

def main():
  parser = argparse.ArgumentParser(description='French translation progress and TSV round-trip')
  parser.add_argument('--missing', action='store_true',
      help='list notes without a French translation')
  parser.add_argument('--export', metavar='FILE.tsv',
      help='export notes to translate as TSV')
  parser.add_argument('--import', dest='import_file', metavar='FILE.tsv',
      help="write the 'french' column of a TSV back into the TOML files")
  parser.add_argument('--level', type=str.lower,
      help="only notes of this JLPT level (n5, n4…) or '-' for notes without level")
  parser.add_argument('--limit', type=int, help='limit the number of notes')
  parser.add_argument('--all', action='store_true',
      help='with --export, also include notes already translated (to review them)')
  args = parser.parse_args()

  if args.import_file:
    import_tsv(args.import_file)
  elif args.export:
    export_tsv(args.export, args.level, args.limit, args.all)
  elif args.missing:
    print_missing(args.level, args.limit)
  else:
    print_report()

if __name__ == '__main__':
  main()
