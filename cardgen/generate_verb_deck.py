#!/usr/bin/env python

"""
Generate Anki deck for verb conjugations.
"""

import genanki
import glob
import re
import sys
import toml
from argparse import ArgumentParser
from collections import OrderedDict
from toml.decoder import TomlDecoder
from toml.encoder import TomlEncoder

OUTPUT_FILENAME = 'japonais_conjugaison_fr.apkg'

def read_verbs():
  def read_notes(filename):
    with open(filename, 'r') as f:
      contents = f.read()
      toml_dict = toml.loads(contents)
      return toml_dict['cards']

  all_notes = []
  for filename in glob.glob('vocabulary/verbs/*.toml', recursive=True):
    if 'cardgen' in filename or 'temp/' in filename:
      continue # XXX: Things here shouldn't be processed for now.
    print('Loading file: {0}'.format(filename))
    notes = read_notes(filename)
    for n in notes:
      if 'disabled' in n and n['disabled']:
        continue
      all_notes.append(n)
  return all_notes

verbs = read_verbs()

# Words starting with an aspirated 'h' don't take elision (ne hurle pas, se hâter).
H_ASPIRE_PREFIXES = ('hach', 'haï', 'hair', 'hal', 'hant', 'harcel', 'hasard', 'hât',
    'hauss', 'heurt', 'hiss', 'hont', 'hurl')

def elide(word, following):
  """elide('ne', 'aime') -> "n'aime"; elide('se', 'lever') -> 'se lever'."""
  first = following[:1].lower()
  if first in 'aàâeéèêëiîïoôuùûyœ' or (first == 'h' and not following.lower().startswith(H_ASPIRE_PREFIXES)):
    return word[:-1] + "'" + following
  return word + ' ' + following

class Verb:
  # Godan Ending -> Masu Stem
  # 'u' -> 'i' sound
  GODAN_TO_MASU_STEM = {
    'う' : 'い',
    'く' : 'き',
    'ぐ' : 'ぎ',
    'す' : 'し',
    'つ' : 'ち',
    'ぬ' : 'に',
    'ぶ' : 'び',
    'む' : 'み',
    'る' : 'り',
  }

  # 'u' -> 'a' sound
  # Used for present indicative plain negative
  GODAN_TO_NAI = {
    'う' : 'わ', # exception!
    'く' : 'か',
    'ぐ' : 'が',
    'す' : 'さ',
    'つ' : 'た',
    'ぬ' : 'な',
    'ぶ' : 'ば',
    'む' : 'ま',
    'る' : 'ら', # godan-ru, not ichidan!
  }

  GODAN_TO_TE = {
    'う' : 'って',
    'く' : 'いて',
    'ぐ' : 'いで',
    'す' : 'して',
    'つ' : 'って',
    'ぬ' : 'んで',
    'ぶ' : 'んで',
    'む' : 'んで',
    'る' : 'って', # godan-ru, not ichidan!
  }

  GODAN_TO_TA = {
    'う' : 'った',
    'く' : 'いた',
    'ぐ' : 'いだ', # what
    'す' : 'した', # wow
    'つ' : 'った',
    'ぬ' : 'んだ',
    'ぶ' : 'んだ',
    'む' : 'んだ',
    'る' : 'った', # godan-ru, not ichidan!
  }

  GODAN_TO_PLAIN_VOLITIONAL = {
    'う' : 'おう',
    'く' : 'こう',
    'ぐ' : 'ごう',
    'す' : 'そう',
    'つ' : 'とう',
    'ぬ' : 'のう',
    'ぶ' : 'ぼう',
    'む' : 'もう',
    'る' : 'ろう', # godan-ru, not ichidan!
  }

  # NB/NOTE: The 'ru' here is 'godan-ru', not 'ichidan'!
  # In the case of provisional verbs, it does not matter.
  ENDING_U_TO_E = {
    'う' : 'え',
    'く' : 'け',
    'ぐ' : 'げ',
    'す' : 'せ',
    'つ' : 'て',
    'ぬ' : 'ね',
    'ぶ' : 'べ',
    'む' : 'め',
    'る' : 'れ', # godan-ru
  }

  def __init__(self, verb_dict):
    self.level = verb_dict['level'] if 'level' in verb_dict else None
    self.group = verb_dict['verb-type']
    self.kanji = verb_dict['kanji']
    self.kana = verb_dict['kana']

    self.french_summary = verb_dict.get('french') or verb_dict['english']
    self.french = verb_dict.get('french-conjugated', {})

  def present_indicative(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Present Indicative form.
    Means "[Verb]", "Will [Verb]", or "Don't/Won't [Verb]"
    """
    if polite:
      if positive:
        return self._masu(kanji=kanji)
      else:
        return self._masen(kanji=kanji)
    else:
      if positive:
        return self.kanji if kanji else self.kana
      else:
        return self._nai(kanji=kanji)

  def presumptive(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Presumptive form.
    Means "Will Probably [Verb]" or "Will Probably Not [Verb]"
    """
    verb = self.present_indicative(polite=False, positive=positive, kanji=kanji)
    suffix = "でしょう" if polite else "だろう"
    return verb + suffix

  def volitional(self, polite=False, kanji=False):
    """
    Return the verb in Volitional form.
    Means "Let's [Verb]". There is no negative.
    """
    verb = self.present_indicative(positive=True, polite=polite, kanji=kanji)
    if polite:
      return re.sub('ます$', 'ましょう', verb)
    else:
      if self.group == 'ichidan':
        return re.sub('る$', 'よう', verb)
      else:
        for godan_end, ending in Verb.GODAN_TO_PLAIN_VOLITIONAL.items():
          if verb.endswith(godan_end):
            return re.sub(godan_end + '$', ending, verb)

  def imperative(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Imperative form.
    Means "Do [Verb]!" or "Do Not [Verb]!"
    """
    if polite:
      if positive:
        base = self._te(kanji=kanji)
      else:
        # eg. aruku -> arukanai de kudasai
        verb = self.present_indicative(polite=False, positive=False, kanji=kanji)
        base = verb + 'で'
      return base + 'ください'
    else:
      if positive:
        verb = self.present_indicative(polite=polite, positive=positive, kanji=kanji)
        if self.group == 'ichidan':
          return re.sub('る$', 'ろ', verb)
        else:
          for godan_end, ending in Verb.ENDING_U_TO_E.items():
            if verb.endswith(godan_end):
              return re.sub(godan_end + '$', ending, verb)
      else:
        dictionary = self.kanji if kanji else self.kana
        return dictionary + 'な'

  def past_indicative(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Past Indicative form.
    Means "[Verb]ed"/"Have [Verb]ed" or "Didn't [Verb]"/"Haven't [Verb]ed"
    """
    if polite:
      verb = self.present_indicative(polite=True, positive=positive, kanji=kanji)
      if positive:
        return re.sub('ます$', 'ました', verb)
      else:
        return verb + 'でした'
    else:
      if positive:
        return self._ta(kanji=kanji)
      else:
        verb = self.present_indicative(positive=False, polite=False, kanji=kanji)
        return re.sub('い$', 'かった', verb)

  def past_presumptive(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Past Presumptive form.
    Means "Probably [Verb]ed" or "Probably Didn't [Verb]"
    """
    verb = self.past_indicative(polite=False, positive=positive, kanji=kanji)
    suffix = 'でしょう' if polite else 'だろう'
    return verb + suffix

  def present_progressive(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Present Progressive form.
    Means "[Verb]ing" or "Not [Verb]ing"
    """
    te_form_base = self._te(kanji=kanji)
    if polite:
      suffix = 'います' if positive else 'いません'
    else:
      suffix = 'いる' if positive else 'いない'
    return te_form_base + suffix

  def past_progressive(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Past Progressive form.
    Means "Was [Verb]ing" or "Wasn't [Verb]ing"
    """
    te_form_base = self._te(kanji=kanji)
    if polite:
      suffix = 'いました' if positive else 'いませんでした'
    else:
      suffix = 'いた' if positive else 'いなかった'
    return te_form_base + suffix

  def provisional(self, positive=False, kanji=False):
    """
    Return the verb in Provisional form.
    Means "If One [Verb]" or "If One Does Not [Verb]"
    """
    if positive:
      verb = self.kanji if kanji else self.kana
      for before, after in Verb.ENDING_U_TO_E.items():
        if verb.endswith(before):
          base = re.sub(before + '$', after, verb)
          return base + 'ば'
    else:
      verb = self.present_indicative(polite=False, positive=False, kanji=kanji)
      return re.sub('い$', 'ければ', verb)

  def conditional(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Conditional form.
    Means "If One [Verb]" or "If One Does Not [Verb]"
    """
    base = self.past_indicative(polite=polite, positive=positive, kanji=kanji)
    return base + 'ら'

  def potential(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Potential form.
    Means "Can [Verb]" or "Cannot [Verb]"
    """
    verb = self.kanji if kanji else self.kana
    if self.group == 'ichidan':
      base = re.sub('る$', 'られ', verb)
    else:
      for before, after in Verb.ENDING_U_TO_E.items():
        if verb.endswith(before):
          base = re.sub(before + '$', after, verb)
          break
    if polite:
      return base + 'ます' if positive else base + 'ません'
    else:
      return base + 'る' if positive else base + 'ない'

  def causative(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Causative form.
    Means "Make or Let (Somebody) [Verb]" or "Not Make or Let (Somebody) [Verb]"
    """
    if self.group == 'ichidan':
      base = self.kanji if kanji else self.kana
      base = re.sub('る$', 'さ', base)
    else:
      nai_form = self._nai(kanji=kanji)
      base = re.sub('ない$', '', nai_form)
    if polite:
      suffix = 'せます' if positive else 'せません'
    else:
      suffix = 'せる' if positive else 'せない'
    return base + suffix

  def passive(self, polite=False, positive=False, kanji=False):
    """
    Return the verb in Passive form.
    Means "Be [Verb]" or "Not Be [Verb]"
    """
    if self.group == 'ichidan':
      base = self.kanji if kanji else self.kana
      base = re.sub('る$', 'ら', base)
    else:
      nai_form = self._nai(kanji=kanji)
      base = re.sub('ない$', '', nai_form)
    if polite:
      suffix = 'れます' if positive else 'れません'
    else:
      suffix = 'れる' if positive else 'れない'
    return base + suffix

  # ==== French ====
  # Built from `french-conjugated` in the TOML: the bare verb forms (infinitif,
  # present, participe, auxiliaire, imperatif, nous) plus `pronominal` and an
  # optional `complement` placed after the verb (eg. aller *ensemble*).

  FRENCH_REQUIRED = ('infinitif', 'present', 'participe', 'auxiliaire', 'imperatif', 'nous')

  def has_french(self):
    return all(str(self.french.get(key, '')).strip() for key in Verb.FRENCH_REQUIRED)

  def _fr_pronominal(self):
    return self.french.get('pronominal') in (True, 'oui')

  def _fr_tail(self, phrase):
    complement = self.french.get('complement', '').strip()
    return '{} {}'.format(phrase, complement) if complement else phrase

  def _fr_conj(self, verb, positive, reflexive=False, adverb=None):
    """Conjugated verb with optional 'se', negation and adverb: 'ne s'est sans doute pas'."""
    if reflexive:
      verb = elide('se', verb)
    if positive:
      return '{} {}'.format(verb, adverb) if adverb else verb
    verb = elide('ne', verb)
    return '{} {} pas'.format(verb, adverb) if adverb else verb + ' pas'

  def _fr_infinitive(self, reflexive=True):
    infinitive = self.french['infinitif']
    if reflexive and self._fr_pronominal():
      infinitive = elide('se', infinitive)
    return self._fr_tail(infinitive)

  def _fr_auxiliary(self):
    return 'est' if self._fr_pronominal() or self.french['auxiliaire'] == 'être' else 'a'

  def french_present_indicative(self, positive=False):
    return self._fr_tail(self._fr_conj(self.french['present'], positive, self._fr_pronominal()))

  def french_presumptive(self, positive=False):
    return '{} {}'.format(self._fr_conj('va', positive, adverb='sans doute'), self._fr_infinitive())

  def french_volitional(self):
    verb = self.french['nous'] + ('-nous' if self._fr_pronominal() else '')
    return self._fr_tail(verb) + ' !'

  def french_imperative(self, positive=False):
    verb = self.french['imperatif']
    if self._fr_pronominal():
      verb = verb + '-toi' if positive else elide('ne', elide('te', verb)) + ' pas'
    elif not positive:
      verb = elide('ne', verb) + ' pas'
    return self._fr_tail(verb) + ' !'

  def french_past_indicative(self, positive=False):
    auxiliary = self._fr_conj(self._fr_auxiliary(), positive, self._fr_pronominal())
    return self._fr_tail('{} {}'.format(auxiliary, self.french['participe']))

  def french_past_presumptive(self, positive=False):
    auxiliary = self._fr_conj(self._fr_auxiliary(), positive, self._fr_pronominal(), 'sans doute')
    return self._fr_tail('{} {}'.format(auxiliary, self.french['participe']))

  def french_present_progressive(self, positive=False):
    return '{} en train {}'.format(self._fr_conj('est', positive), elide('de', self._fr_infinitive()))

  def french_past_progressive(self, positive=False):
    return '{} en train {}'.format(self._fr_conj('était', positive), elide('de', self._fr_infinitive()))

  def french_provisional(self, positive=False):
    # NB: Same as french_conditional; the cards tell them apart with a ～ば / ～たら hint.
    return 'si on ' + self.french_present_indicative(positive)

  def french_conditional(self, positive=False):
    return 'si on ' + self.french_present_indicative(positive)

  def french_potential(self, positive=False):
    return '{} {}'.format(self._fr_conj('peut', positive), self._fr_infinitive())

  def french_causative(self, positive=False):
    if self.french['infinitif'] == 'être':
      causative = 'obliger à ' + self._fr_infinitive() # not 'faire être là'
    else:
      # 'faire approcher' rather than 'faire s'approcher'
      causative = 'faire ' + self._fr_infinitive(reflexive=False)
    return causative if positive else 'ne pas ' + causative

  def french_passive(self, positive=False):
    if self.french['infinitif'] == 'être':
      # Adversity passive; 'être été là' isn't French.
      passive = 'subir le fait ' + elide('de', self._fr_infinitive())
    else:
      passive = self._fr_tail('être ' + self.french['participe'])
    return passive if positive else 'ne pas ' + passive

  def _masu(self, kanji=False):
    base = self.kanji if kanji else self.kana
    replaced = None
    if self.group == 'ichidan':
      replaced = re.sub('る$', '', base)
    else:
      for godan_end, stem in Verb.GODAN_TO_MASU_STEM.items():
        if base.endswith(godan_end):
          regex = re.compile(godan_end + '$')
          replaced = regex.sub(stem, base)
          break
    if replaced:
      return replaced + 'ます'

  def _masen(self, kanji=False):
    masu = self._masu(kanji=kanji)
    if masu:
      return re.sub('ます$', 'ません', masu)

  def _nai(self, kanji=False):
    base = self.kanji if kanji else self.kana
    replaced = None
    if self.group == 'ichidan':
      replaced = re.sub('る$', '', base)
    else:
      for godan_end, nai in Verb.GODAN_TO_NAI.items():
        if base.endswith(godan_end):
          regex = re.compile(godan_end + '$')
          replaced = regex.sub(nai, base)
          break
    if replaced:
      return replaced + 'ない'

  def _te(self, kanji=False):
    base = self.kanji if kanji else self.kana
    if self.group == 'ichidan':
      return re.sub('る$', 'て', base)
    else:
      for godan_end, te_form in Verb.GODAN_TO_TE.items():
        if base.endswith(godan_end):
          return re.sub(godan_end + '$', te_form, base)

  def _ta(self, kanji=False):
    base = self.kanji if kanji else self.kana
    if self.group == 'ichidan':
      return re.sub('る$', 'た', base)
    else:
      for godan_end, te_form in Verb.GODAN_TO_TA.items():
        if base.endswith(godan_end):
          return re.sub(godan_end + '$', te_form, base)

VERB_HASH = { verb['kanji'] : Verb(verb) for verb in verbs }

class Conjugation:
  def __init__(self, name, label, has_negative=True, has_polite=True, hint=None):
    self.name = name
    self.label = label # French name shown in Anki
    self.has_negative = has_negative
    self.has_polite = has_polite
    self.hint = hint # Tells apart forms with the same French, eg. ～ば / ～たら

  def conjugation_name(self):
    return self.name.strip().lower().replace(' ', '_')

  def field_names(self):
    # NB: DO NOT CHANGE THE ORDER. APPEND ONLY.
    # Anki has the potential to lose SRS data or get cards/fields out of sync
    # if the field numbers change. The ordering here directly maps to field numberings.
    fields = []

    prefix = self.conjugation_name() + '_'

    fields.append(prefix + 'french_positive')
    if self.has_negative:
      fields.append(prefix + 'french_negative')

    fields.extend([
      prefix + 'plain_positive_kanji',
      prefix + 'plain_positive_kana',
    ])

    if self.has_negative:
      fields.extend([
        prefix + 'plain_negative_kanji',
        prefix + 'plain_negative_kana',
      ])

    if self.has_polite:
      fields.extend([
        prefix + 'polite_positive_kanji',
        prefix + 'polite_positive_kana',
      ])
      if self.has_negative:
        fields.extend([
          prefix + 'polite_negative_kanji',
          prefix + 'polite_negative_kana',
        ])

    return fields

  def map_verb_fields(self, verb):
    # NB: DO NOT CHANGE THE ORDER. APPEND ONLY. Must match field_names().
    field_values = []

    # TODO: Instead of having one monolithic class 'Verb', have a base class
    # and then subclasses that implement each conjugation's rules. Then we
    # don't need to dynamic dispatch, you can just call `conjugate(...)`.
    method_name = self.conjugation_name()
    method = getattr(verb, method_name)
    french_method = getattr(verb, 'french_' + method_name)

    if self.has_negative:
      field_values.extend([
        french_method(positive=True),
        french_method(positive=False),
      ])
    else:
      field_values.append(french_method())

    for polite in ([False, True] if self.has_polite else [None]):
      for positive in ([True, False] if self.has_negative else [None]):
        kwargs = {}
        if polite is not None:
          kwargs['polite'] = polite
        if positive is not None:
          kwargs['positive'] = positive
        field_values.extend([
          method(kanji=True, **kwargs),
          method(kanji=False, **kwargs),
        ])

    return field_values

  def templates(self):
    # NB: DO NOT CHANGE THE ORDER. APPEND ONLY.
    templates = []
    prefix = self.conjugation_name() + '_'
    registers = ['plain', 'polite'] if self.has_polite else ['plain']
    polarities = ['positive', 'negative'] if self.has_negative else ['positive']
    for register in registers:
      for polarity in polarities:
        french_field = prefix + 'french_' + polarity
        japanese_field = '{}{}_{}_'.format(prefix, register, polarity)
        for from_french in (True, False):
          templates.append(self.card_template(
              french_field, japanese_field, register, polarity, from_french))
    return templates

  def card_template(self, french_field, japanese_field, register, polarity, from_french):
    register_label = 'poli' if register == 'polite' else 'neutre'
    details = [register_label] + ([self.hint] if self.hint else [])

    french = '{{{{{}}}}}'.format(french_field)
    japanese = ('<span class="kanji">{{{{{0}kanji}}}}</span> '
        '<span class="kana">{{{{{0}kana}}}}</span>').format(japanese_field)

    if from_french:
      question = '{} <span class="register">({})</span>'.format(french, ', '.join(details))
      answer = japanese
    else:
      question = japanese
      answer = french

    name = '{} {} {} : {}'.format(
        self.label,
        'affirmatif' if polarity == 'positive' else 'négatif',
        register_label,
        'FR → JP' if from_french else 'JP → FR')

    return {
      'name': name,
      'qfmt': '<span class="question">' + question + '</span>',
      'afmt': ANSWER_TEMPLATE.format(question=question, answer=answer, label=self.label),
    }

ANSWER_TEMPLATE = '''
<span class="question">{question}</span>

<hr id="answer">

{answer}

<br>
<br>

<table>
  <tr>
    <th>forme</th>
    <td>{label}</td>
  </tr>
  <tr>
    <th>kanji</th>
    <td>{{{{base_kanji}}}}</td>
  </tr>
  <tr>
    <th>kana</th>
    <td>{{{{base_kana}}}}</td>
  </tr>
  <tr>
    <th>groupe</th>
    <td>{{{{group}}}}</td>
  </tr>
  <tr>
    <th>sens</th>
    <td>{{{{base_french}}}}</td>
  </tr>
  <tr>
    <th>niveau</th>
    <td>{{{{level}}}}</td>
  </tr>
</table>
'''

# NB: DO NOT CHANGE THE ORDER. APPEND ONLY.
# Anki has the potential to lose SRS data or get cards/fields out of sync if
# the field numbers change. The ordering here directly maps to field numberings.
CONJUGATIONS = [
  Conjugation('Present Indicative', 'Présent'),
  Conjugation('Presumptive', 'Présomptif'),
  Conjugation('Volitional', 'Volitif', has_negative=False),
  Conjugation('Imperative', 'Impératif'),
  Conjugation('Past Indicative', 'Passé'),
  Conjugation('Past Presumptive', 'Passé présomptif'),
  Conjugation('Present Progressive', 'Présent progressif'),
  Conjugation('Past Progressive', 'Passé progressif'),
  Conjugation('Provisional', 'Conditionnel en ～ば', has_polite=False, hint='～ば'),
  Conjugation('Conditional', 'Conditionnel en ～たら', hint='～たら'),
  Conjugation('Potential', 'Potentiel'),
  Conjugation('Causative', 'Causatif'),
  Conjugation('Passive', 'Passif'),
]

# use random.randrange(1 << 30, 1 << 31) to generate a suitable model_id,
# and hardcode it into your Model definition.

VERB_CARD_DECK = genanki.Deck(
  1461826981, # XXX: DO NOT CHANGE
  'Japonais généré - conjugaison') # XXX: DO NOT CHANGE

MODEL_FIELDS = [
  # NB: Make changes to the Anki deck model fields using the
  # Anki interface first, or imports won't work as expected.
  {'name': 'base_kanji'},
  {'name': 'base_kana'},
  {'name': 'base_french'},
  {'name': 'group'},
  {'name': 'level'},
]

TEMPLATES = []

for conjugation in CONJUGATIONS:
  fields = [{'name': field_name } for field_name in conjugation.field_names()]
  MODEL_FIELDS.extend(fields)

  TEMPLATES.extend(conjugation.templates())


VERB_CARD_MODEL = genanki.Model(
  # XXX: DO NOT CHANGE
  1275647302,

  # The name of the model can change.
  'Modèle conjugaison japonaise (FR)',

  # NB: Make changes to the Anki deck model fields using the
  # Anki interface first, or imports won't work as expected.
  fields=MODEL_FIELDS,

  # NB: Add or remove templates (with the same names) using the
  # Anki interface first, or imports won't work as expected.
  templates=TEMPLATES,

  css = '''
.card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: black;
  background-color: white;
}

.question {
  font-size: 1.5em;
}

.register {
  color: #888;
  font-size: 0.6em;
}

.kana {
  color: #00f;
}

.kana:before { content: '(' }
.kana:after { content: ')' }

table {
  border: 1px solid #ccc;
  margin: auto;
}
''')

class Note(genanki.Note):
  def __init__(self, verb):
    self.kanji = verb.kanji
    self.kana = verb.kana
    self.group = verb.group
    self.french_summary = verb.french_summary
    self.level = verb.level
    #self.tags = verb_dict['tags'] if 'tags' in verb_dict else []
    self.tags = ['verb']

    #if self.level:
    #  self.tags.append(self.level)

    # NB: Must match order of model.
    fields = [
      self.kanji,
      self.kana,
      self.french_summary,
      self.group,
      self.level,
    ]

    for conjugation in CONJUGATIONS:
      fields.extend(conjugation.map_verb_fields(verb))

    # NB: genanki requires string fields; missing values (eg. no JLPT level) are None.
    fields = ['' if f is None else f for f in fields]

    super().__init__(model=VERB_CARD_MODEL,
        fields=fields,
        sort_field=self.kana,
        tags=self.tags,
        guid=None)

  @property
  def guid(self):
    # These can actually match across decks and models, so be careful! If you use the
    # same guid for notes in another model/deck, you'll confuse Anki on import.
    return genanki.guid_for('verb_conjugation', self.kanji, self.kana, self.group)

  #def card_count(self):
  #  if self.make_kanji_card == 'y':
  #    if self.make_hiragana_only_card == 'y':
  #      return 3
  #    else:
  #      return 2
  #  return 2

def main():
  for verb in VERB_HASH.values():
    if not verb.has_french():
      print('Skipping {} ({}): incomplete french-conjugated'.format(verb.kanji, verb.kana))
      continue
    note = Note(verb)
    VERB_CARD_DECK.add_note(note)

  genanki.Package(VERB_CARD_DECK).write_to_file(OUTPUT_FILENAME)

if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('--test', help='run the unit tests', action="store_true")
  args = parser.parse_args()

  if args.test:
    from generate_verb_deck_tests import *

    sys.argv.remove('--test') # passed to unittest module and blows up
    unittest.main()
  else:
    main()

