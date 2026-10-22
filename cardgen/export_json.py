#!/usr/bin/env python

"""
Export both decks to app/public/deck.json for the review app (see roadmap-app.md).

Uses the same notes as the Anki decks, so config/*.txt and the French fallbacks apply.
Run from the repository root: python cardgen/export_json.py
"""

import hashlib
import json
import os

import generate_verb_deck as verb_deck
import generate_vocabulary_deck as vocabulary_deck
from update_frequencies import ANIME_FREQUENCY_SUBFIELD

OUTPUT_FILENAME = 'app/public/deck.json'

# Bump when the structure of deck.json changes, so the app can refuse files it can't read.
FORMAT_VERSION = 1

# Card types of the vocabulary deck, in the same order as the Anki templates.
VOCABULARY_CARD_TYPES = [
  {'id': 'fr-jp', 'label': 'Français → Japonais'},
  {'id': 'furigana', 'label': 'Kanji + Kana'},
  {'id': 'kanji', 'label': 'Kanji seul'},
  {'id': 'kana', 'label': 'Kana seul'},
]

def vocabulary_note(note):
  cards = ['fr-jp']
  if note.make_furigana_card:
    cards.append('furigana')
  if note.make_kanji_card:
    cards.append('kanji')
  if note.make_hiragana_only_card:
    cards.append('kana')

  frequency = None
  if note.frequency_highest:
    frequency = {'score': int(note.frequency_highest), 'source': note.frequency_highest_source}
    if note.frequency_anime:
      frequency[ANIME_FREQUENCY_SUBFIELD] = int(note.frequency_anime)

  # Anki tags also carry the level and suspension, which have their own fields here.
  tags = [tag for tag in note.tags if tag not in (note.level, 'suspended', 'suspended_by_config')]

  return {
    'id': note.guid,
    'kanji': note.kanji,
    'kana': note.kana,
    'romaji': note.romaji,
    'french': note.french,
    'level': note.level or None,
    'tags': tags,
    'frequency': frequency,
    'suspended': note.suspended,
    'cards': cards,
  }

def export_vocabulary():
  notes, _ = vocabulary_deck.load_notes()
  # Anki keeps a single note per guid (kanji + kana); so do we, keeping the first one.
  by_id = {}
  duplicates = []
  for note in notes:
    if note.guid in by_id:
      duplicates.append(note)
      continue
    by_id[note.guid] = vocabulary_note(note)
  return {
    'name': vocabulary_deck.KANJI_CARD_DECK.name,
    'card_types': VOCABULARY_CARD_TYPES,
    'notes': list(by_id.values()),
  }, duplicates

def form_id(register, polarity):
  return '{}.{}'.format(register, polarity)

def export_conjugation():
  conjugations = [{
    'id': conjugation.conjugation_name(),
    'label': conjugation.label,
    'hint': conjugation.hint,
    'forms': [form_id(register, polarity) for register, polarity in conjugation.forms()],
  } for conjugation in verb_deck.CONJUGATIONS]

  notes = []
  skipped = []
  for verb in verb_deck.VERB_HASH.values():
    if not verb.has_french():
      skipped.append(verb)
      continue
    note = verb_deck.Note(verb)
    forms = {}
    for conjugation in verb_deck.CONJUGATIONS:
      method = getattr(verb, conjugation.conjugation_name())
      french_method = getattr(verb, 'french_' + conjugation.conjugation_name())
      for register, polarity in conjugation.forms():
        kwargs = {}
        french_kwargs = {}
        if conjugation.has_polite:
          kwargs['polite'] = register == 'polite'
        if conjugation.has_negative:
          kwargs['positive'] = french_kwargs['positive'] = polarity == 'positive'
        kana = method(kanji=False, **kwargs)
        forms['{}.{}'.format(conjugation.conjugation_name(), form_id(register, polarity))] = {
          'kanji': method(kanji=True, **kwargs),
          'kana': kana,
          'romaji': verb_deck.to_romaji(kana),
          'french': french_method(**french_kwargs),
        }
    notes.append({
      'id': note.guid,
      'kanji': verb.kanji,
      'kana': verb.kana,
      'romaji': verb_deck.to_romaji(verb.kana),
      'french': verb.french_summary,
      'group': verb.group,
      'level': verb.level,
      'forms': forms,
    })

  return {
    'name': verb_deck.VERB_CARD_DECK.name,
    # Every form gives two cards: '<conjugation>.<register>.<polarity>.fr-jp' and '….jp-fr'.
    'directions': ['fr-jp', 'jp-fr'],
    'conjugations': conjugations,
    'notes': notes,
  }, skipped

def main():
  vocabulary, duplicates = export_vocabulary()
  conjugation, skipped = export_conjugation()

  decks = {'vocabulary': vocabulary, 'conjugation': conjugation}
  # The version is a hash of the content: it only changes when the decks do.
  content = json.dumps(decks, ensure_ascii=False, sort_keys=True)
  version = hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
  deck = {'format': FORMAT_VERSION, 'version': version, 'decks': decks}

  os.makedirs(os.path.dirname(OUTPUT_FILENAME), exist_ok=True)
  with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
    json.dump(deck, f, ensure_ascii=False, separators=(',', ':'))

  vocabulary_cards = sum(len(n['cards']) for n in vocabulary['notes'])
  conjugation_cards = sum(len(n['forms']) * 2 for n in conjugation['notes'])
  print('Vocabulary: {} notes, {} cards ({} duplicates skipped)'.format(
      len(vocabulary['notes']), vocabulary_cards, len(duplicates)))
  for note in duplicates:
    print('  > duplicate: {} ({})'.format(note.kanji, note.kana))
  print('Conjugation: {} verbs, {} cards ({} incomplete skipped)'.format(
      len(conjugation['notes']), conjugation_cards, len(skipped)))
  print('Version: {}'.format(version))
  print('Output file: {} ({:.1f} Mo)'.format(
      OUTPUT_FILENAME, os.path.getsize(OUTPUT_FILENAME) / 1e6))

if __name__ == '__main__':
  main()
