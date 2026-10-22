#!/usr/bin/env python

"""
Generate Anki deck for vocabulary.
"""

import genanki
import glob
import re
import sys
import toml
import unittest
from argparse import ArgumentParser
from collections import OrderedDict
from functools import cached_property
from romaji import to_romaji
from toml.decoder import TomlDecoder
from toml.encoder import TomlEncoder

from update_frequencies import ANIME_FREQUENCY_SUBFIELD
from update_frequencies import FREQUENCY_FIELD
from update_frequencies import calculate_highest_frequency

OUTPUT_FILENAME = 'japonais_fr.apkg'

# use random.randrange(1 << 30, 1 << 31) to generate a suitable model_id,
# and hardcode it into your Model definition.

KANJI_CARD_DECK = genanki.Deck(
  2080406641, # XXX: DO NOT CHANGE
  'Japonais généré') # XXX: DO NOT CHANGE

KANJI_CARD_MODEL = genanki.Model(
  1405375075, # XXX: DO NOT CHANGE
  'Modèle japonais (FR)', # The name of the model can change.
  fields=[
    # NB: Make changes to the Anki deck model fields using the
    # Anki interface first, or imports won't work as expected.
    # Even additive changes MUST be made in Anki's UI first, or
    # you wind up with a new deck 'Modèle japonais (FR)-{hash}'
    {'name': 'Kanji'},
    {'name': 'Kana'},
    {'name': 'Français'},
    {'name': 'Carte furigana ?'},
    {'name': 'Carte kanji seul ?'},
    {'name': 'Carte kana seul ?'},
    {'name': 'Niveau'},
    {'name': 'Fréquence max'},
    {'name': 'Source fréquence'},
    {'name': 'Fréquence anime'},
    {'name': 'Romaji'},
  ],
  # NB: Add or remove templates (with the same names) using the
  # Anki interface first, or imports won't work as expected.
  templates=[
    # Card 1 - Front: French; Back: French + Kanji + Kana
    {
      'name': 'Français → Japonais',
      'qfmt': '''
{{Français}}

<footer>
  <div class="level level-{{Niveau}}">{{Niveau}}</div>
  {{#Fréquence max}}
    <div class="frequency">
      {{Fréquence max}} ({{Source fréquence}})
      {{#Fréquence anime}}
        <br />
        {{Fréquence anime}} (anime)
      {{/Fréquence anime}}
    </div>
  {{/Fréquence max}}
</footer>
''',
      'afmt': '''
{{Français}}

<hr id="answer">

<div>{{Kanji}}</div>
<div id="hint">{{Kana}}</div>
{{#Romaji}}<div class="romaji">{{Romaji}}</div>{{/Romaji}}

<footer>
  <div class="level level-{{Niveau}}">{{Niveau}}</div>
  {{#Fréquence max}}
    <div class="frequency">
      {{Fréquence max}} ({{Source fréquence}})
      {{#Fréquence anime}}
        <br />
        {{Fréquence anime}} (anime)
      {{/Fréquence anime}}
    </div>
  {{/Fréquence max}}
</footer>
'''
    },
    # Card 2 (Optional) - Furigana (Kanji + Kana); Back: French + Kanji + Kana
    # This exists as an independent card instead of using doubly nested mustache
    # conditionals due to weirdness in Anki about not generating cards when imports
    # happen. This is the most clear-cut way to ensure card generation happens.
    # Something about doubly-nested if statements prevents Anki's bulk importing from
    # making such cards, even if they're non-blank. (They may only evaluate the first
    # level of if-statements during import...)
    {
      'name': 'Kanji + Kana',
      'qfmt': '''
{{#Carte furigana ?}}
  <div>{{Kanji}}</div>
  <div id="hint">({{Kana}})</div>

  <footer>
    <div class="level level-{{Niveau}}">{{Niveau}}</div>
    {{#Fréquence max}}
      <div class="frequency">
        {{Fréquence max}} ({{Source fréquence}})
        {{#Fréquence anime}}
          <br />
          {{Fréquence anime}} (anime)
        {{/Fréquence anime}}
      </div>
    {{/Fréquence max}}
  </footer>
{{/Carte furigana ?}}
''',
      'afmt': '''
{{#Carte furigana ?}}
  <div>{{Kanji}}</div>
  <div id="hint">({{Kana}})</div>
{{/Carte furigana ?}}

<hr id="answer">

{{#Romaji}}<div class="romaji">{{Romaji}}</div>{{/Romaji}}

<div>{{Français}}</div>

<footer>
  <div class="level level-{{Niveau}}">{{Niveau}}</div>
  {{#Fréquence max}}
    <div class="frequency">
      {{Fréquence max}} ({{Source fréquence}})
      {{#Fréquence anime}}
        <br />
        {{Fréquence anime}} (anime)
      {{/Fréquence anime}}
    </div>
  {{/Fréquence max}}
</footer>
'''
    },
    # Card 3 (Optional) - Front: Kanji (only); Back: French + Kanji + Kana
    {
      'name': 'Kanji seul (optionnel)',
      'qfmt': '''
{{#Carte kanji seul ?}}
  {{Kanji}}

  <footer>
    <div class="level level-{{Niveau}}">{{Niveau}}</div>
    {{#Fréquence max}}
      <div class="frequency">
        {{Fréquence max}} ({{Source fréquence}})
        {{#Fréquence anime}}
          <br />
          {{Fréquence anime}} (anime)
        {{/Fréquence anime}}
      </div>
    {{/Fréquence max}}
  </footer>
{{/Carte kanji seul ?}}
''',
      'afmt': '''
<div>{{Kanji}}</div>

<hr id="answer">

<div id="hint">({{Kana}})</div>
{{#Romaji}}<div class="romaji">{{Romaji}}</div>{{/Romaji}}

<div>{{Français}}</div>

<footer>
  <div class="level level-{{Niveau}}">{{Niveau}}</div>
  {{#Fréquence max}}
    <div class="frequency">
      {{Fréquence max}} ({{Source fréquence}})
      {{#Fréquence anime}}
        <br />
        {{Fréquence anime}} (anime)
      {{/Fréquence anime}}
    </div>
  {{/Fréquence max}}
</footer>
'''
    },
    # Card 4 (Optional) - Front: Hiragana (only); Back: French + Kanji + Kana
    {
      'name': 'Kana seul (optionnel)',
      'qfmt': '''
{{#Carte kana seul ?}}
  {{Kana}}

  <footer>
    <div class="level level-{{Niveau}}">{{Niveau}}</div>
    {{#Fréquence max}}
      <div class="frequency">
        {{Fréquence max}} ({{Source fréquence}})
        {{#Fréquence anime}}
          <br />
          {{Fréquence anime}} (anime)
        {{/Fréquence anime}}
      </div>
    {{/Fréquence max}}
  </footer>
{{/Carte kana seul ?}}
''',
      'afmt': '''
<div>{{Kana}}</div>

<hr id="answer">

<div id="hint">({{Kanji}})</div>
{{#Romaji}}<div class="romaji">{{Romaji}}</div>{{/Romaji}}

<div>{{Français}}</div>

<footer>
  <div class="level level-{{Niveau}}">{{Niveau}}</div>
  {{#Fréquence max}}
    <div class="frequency">
      {{Fréquence max}} ({{Source fréquence}})
      {{#Fréquence anime}}
        <br />
        {{Fréquence anime}} (anime)
      {{/Fréquence anime}}
    </div>
  {{/Fréquence max}}
</footer>
'''
    },
  ],
  css = '''
.card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: black;
  background-color: white;
}

#hint {
  color: #00f;
}

#hint div {
  display: inline;
}

.romaji {
  color: #888;
  font-style: italic;
}

footer {
  border-top: 1px dashed #888;
  color: #888;
  margin-top: 1em;
  padding-top: 0.3em;
}

.level {
  float: left;
}

.frequency {
  float: right;
  text-transform: capitalize;
}
  ''')

class Note(genanki.Note):
  def __init__(self, verb_dict, suspended=False):
    # These fields are always populated:
    self.kanji = verb_dict['kanji']
    self.kana = verb_dict['kana']
    self.romaji = to_romaji(self.kana)
    # These fields are not always populated:
    self.level = verb_dict['level'] if 'level' in verb_dict else ''
    # NB: Anki tags can't contain spaces, so 'suru verb' becomes 'suru_verb'.
    self.tags = [tag.replace(' ', '_') for tag in verb_dict.get('tags', [])]

    # Fall back to English until the note is translated; search 'tag:a_traduire' in Anki.
    self.translated = bool(verb_dict.get('french', '').strip())
    if self.translated:
      self.french = verb_dict['french']
    else:
      self.french = verb_dict['english']
      self.tags.append('a_traduire')
    self.frequency_highest = ''
    self.frequency_highest_source = ''
    self.frequency_anime = ''

    # Suspended notes will not show up for review until removed from suspension.
    self.suspended = suspended

    if self.level:
      self.tags.append(self.level)

    if self.suspended:
      # NB: This isn't functional, but helps manually searching for suspended cards.
      # At present, the 'suspended' scheduling does not work correctly to suspend cards.
      self.tags.append('suspended')
      self.tags.append('suspended_by_config')

    if 'make_kanji_card' in verb_dict and verb_dict['make_kanji_card']:
      self.make_kanji_card = 'y'
      self.make_furigana_card = ''
    else:
      self.make_kanji_card = ''
      self.make_furigana_card = 'y'

    if 'make_hiragana_only_card' in verb_dict and verb_dict['make_hiragana_only_card']:
      self.make_hiragana_only_card = 'y'
    else:
      self.make_hiragana_only_card = ''

    # TODO: Rename the Anki fields to frequency_* rather than highest_frequency_* to match
    # the new field naming scheme.
    if FREQUENCY_FIELD in verb_dict:
      frequency_data = verb_dict[FREQUENCY_FIELD]
      highest_frequency = calculate_highest_frequency(frequency_data)
      if highest_frequency:
        self.frequency_highest = str(highest_frequency['score'])
        self.frequency_highest_source = highest_frequency['source']
        # Only include additional anime frequency if it's not the highest
        if highest_frequency['source'] != ANIME_FREQUENCY_SUBFIELD \
            and ANIME_FREQUENCY_SUBFIELD in frequency_data:
          self.frequency_anime = str(frequency_data[ANIME_FREQUENCY_SUBFIELD])

    sort_field = self.kana

    # NB: Must match order of model.
    # Even additive changes MUST be made in Anki's UI first, or you wind up with a new
    # deck called 'Generated Japanese Model-{hash}'
    fields = [
      self.kanji,
      self.kana,
      self.french,
      self.make_furigana_card,
      self.make_kanji_card,
      self.make_hiragana_only_card,
      self.level,
      self.frequency_highest,
      self.frequency_highest_source,
      self.frequency_anime,
      self.romaji,
    ]

    super().__init__(model=KANJI_CARD_MODEL,
        fields=fields,
        sort_field=self.kana,
        tags=self.tags,
        guid=None)

  @property
  def guid(self):
    return genanki.guid_for(self.kanji, self.kana)

  @cached_property
  def cards(self):
    # We use cached_property instead of initializing in the constructor so that
    # the user can set the model after calling __init__ and it'll still work.
    rv = []
    for card_ord, any_or_all, required_field_ords in self.model._req:
      op = {'any': any, 'all': all}[any_or_all]
      if op(self.fields[ord_] for ord_ in required_field_ords):
        rv.append(genanki.Card(card_ord, suspend=self.suspended))
    return rv

  def card_count(self):
    if self.make_kanji_card == 'y':
      if self.make_hiragana_only_card == 'y':
        return 3
      else:
        return 2
    return 2

def read_set(filename):
  lines = []
  with open(filename, 'r') as f:
    lines = f.readlines()
    lines = map(lambda x: x.strip(), lines)
    lines = filter(None, lines)
  return set(lines)

KANJI_ONLY_VOCAB = read_set('config/kanji-only-vocab.txt')
SUSPENDED_VOCAB = read_set('config/suspended.txt')

def read_vocabulary_notes(filename):
  with open(filename, 'r') as f:
    contents = f.read()
    toml_dict = toml.loads(contents)
    return toml_dict['cards']

def load_notes():
  """
  Read every vocabulary note, applying config/kanji-only-vocab.txt and config/suspended.txt.
  Returns (notes, number of disabled notes skipped).
  """
  notes = []
  total_disabled = 0 # TODO: Deprecate and remove
  for filename in sorted(glob.glob('**/*.toml', recursive=True)):
    if 'cardgen' in filename or 'temp/' in filename:
      continue # XXX: Things here shouldn't be processed for now.
    print('Loading file: {0}'.format(filename))
    for n in read_vocabulary_notes(filename):
      if 'disabled' in n and n['disabled']:
        total_disabled += 1 # TODO: Deprecate and remove
        continue

      if 'kanji' not in n:
        raise Exception("Key 'kanji' not in note: {}".format(n))

      if n['kanji'] in KANJI_ONLY_VOCAB:
        n['make_kanji_card'] = True
        n['make_hiragana_only_card'] = False

      suspended = n['kanji'] in SUSPENDED_VOCAB
      notes.append(Note(n, suspended=suspended))
  return notes, total_disabled

def main():
  notes, total_disabled = load_notes()

  total_notes = 0
  total_cards = 0
  total_suspended = 0
  total_kanji_only = 0
  total_hiragana_only = 0
  total_translated = 0

  for note in notes:
    if note.suspended:
      total_suspended += 1
    if note.make_kanji_card:
      total_kanji_only += 1
    if note.make_hiragana_only_card:
      total_hiragana_only += 1
    if note.translated:
      total_translated += 1

    KANJI_CARD_DECK.add_note(note)
    total_notes += 1
    total_cards += note.card_count()

  print('Total cards: {0}'.format(total_cards))
  print('Total notes: {0}'.format(total_notes))
  print('  > notes disabled (deprecated): {0}'.format(total_disabled))
  print('  > notes suspended: {0}'.format(total_suspended))
  print('  > notes /w kanji-only cards: {0}'.format(total_kanji_only))
  print('  > notes w/ hiragana-only cards: {0}'.format(total_hiragana_only))
  print('  > notes translated to French: {0} / {1}'.format(total_translated, total_notes))
  print('Output file: {0}'.format(OUTPUT_FILENAME))

  genanki.Package(KANJI_CARD_DECK).write_to_file(OUTPUT_FILENAME)

if __name__ == '__main__':
  main()
