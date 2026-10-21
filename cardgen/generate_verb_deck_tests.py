import genanki
import glob
import re
import sys
import toml
import unittest
from argparse import ArgumentParser
from collections import OrderedDict
from toml.decoder import TomlDecoder
from toml.encoder import TomlEncoder

from generate_verb_deck import CONJUGATIONS
from generate_verb_deck import Conjugation
from generate_verb_deck import VERB_HASH
from generate_verb_deck import Verb
from generate_verb_deck import elide

class TestJapaneseVerbConjugation(unittest.TestCase):

  def test_present_indicative(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].present_indicative(polite, positive, kanji)
    # Polite
    self.assertEqual(v('歩く', True, True, True), '歩きます')
    self.assertEqual(v('歩く', True, True, False), 'あるきます')
    self.assertEqual(v('歩く', True, False, True), '歩きません')
    self.assertEqual(v('歩く', True, False, False), 'あるきません')
    # Plain
    self.assertEqual(v('歩く', False, True, True), '歩く')
    self.assertEqual(v('歩く', False, True, False), 'あるく')
    self.assertEqual(v('歩く', False, False, True), '歩かない')
    self.assertEqual(v('歩く', False, False, False), 'あるかない')

  def test_presumptive(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].presumptive(polite, positive, kanji)
    # Polite
    self.assertEqual(v('言う', True, True, True), '言うでしょう')
    self.assertEqual(v('言う', True, True, False), 'いうでしょう')
    self.assertEqual(v('噛む', True, False, True), '噛まないでしょう')
    self.assertEqual(v('噛む', True, False, False), 'かまないでしょう')
    # Plain
    self.assertEqual(v('噛む', False, True, True), '噛むだろう')
    self.assertEqual(v('噛む', False, True, False), 'かむだろう')
    self.assertEqual(v('言う', False, False, True), '言わないだろう')
    self.assertEqual(v('言う', False, False, False), 'いわないだろう')

  def test_volitional(self):
    def v(verb, polite, kanji):
      return VERB_HASH[verb].volitional(polite, kanji)
    # Polite
    self.assertEqual(v('浴びる', True, True), '浴びましょう')
    self.assertEqual(v('浴びる', True, False), 'あびましょう')
    # Plain
    self.assertEqual(v('謝る', False, True), '謝ろう')
    self.assertEqual(v('謝る', False, False), 'あやまろう')

  def test_imperative(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].imperative(polite, positive, kanji)
    # Polite
    self.assertEqual(v('見る', True, True, True), '見てください')
    self.assertEqual(v('見る', True, True, False), 'みてください')
    self.assertEqual(v('読む', True, False, True), '読まないでください')
    self.assertEqual(v('読む', True, False, False), 'よまないでください')
    # Plain
    self.assertEqual(v('見る', False, True, True), '見ろ')
    self.assertEqual(v('見る', False, True, False), 'みろ')
    self.assertEqual(v('読む', False, False, True), '読むな')
    self.assertEqual(v('読む', False, False, False), 'よむな')

  def test_past_indicative(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].past_indicative(polite, positive, kanji)
    # Polite
    self.assertEqual(v('読む', True, True, True), '読みました')
    self.assertEqual(v('読む', True, True, False), 'よみました')
    self.assertEqual(v('読む', True, False, True), '読みませんでした')
    self.assertEqual(v('読む', True, False, False), 'よみませんでした')
    # Plain
    self.assertEqual(v('読む', False, True, True), '読んだ')
    self.assertEqual(v('読む', False, True, False), 'よんだ')
    self.assertEqual(v('読む', False, False, True), '読まなかった')
    self.assertEqual(v('読む', False, False, False), 'よまなかった')

  def test_past_presumptive(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].past_presumptive(polite, positive, kanji)
    # Polite
    self.assertEqual(v('遊ぶ', True, True, True), '遊んだでしょう')
    self.assertEqual(v('遊ぶ', True, True, False), 'あそんだでしょう')
    self.assertEqual(v('遊ぶ', True, False, True), '遊ばなかったでしょう')
    self.assertEqual(v('遊ぶ', True, False, False), 'あそばなかったでしょう')
    # Plain
    self.assertEqual(v('遊ぶ', False, True, True), '遊んだだろう')
    self.assertEqual(v('遊ぶ', False, True, False), 'あそんだだろう')
    self.assertEqual(v('遊ぶ', False, False, True), '遊ばなかっただろう')
    self.assertEqual(v('遊ぶ', False, False, False), 'あそばなかっただろう')

  def test_present_progressive(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].present_progressive(polite, positive, kanji)
    # Polite
    self.assertEqual(v('泣く', True, True, True), '泣いています')
    self.assertEqual(v('泣く', True, True, False), 'ないています')
    self.assertEqual(v('近づく', True, False, True), '近づいていません')
    self.assertEqual(v('近づく', True, False, False), 'ちかづいていません')
    # Plain
    self.assertEqual(v('決める', False, True, True), '決めている')
    self.assertEqual(v('決める', False, True, False), 'きめている')
    self.assertEqual(v('打つ', False, False, True), '打っていない')
    self.assertEqual(v('打つ', False, False, False), 'うっていない')

  def test_past_progressive(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].past_progressive(polite, positive, kanji)
    # Polite
    self.assertEqual(v('走る', True, True, True), '走っていました')
    self.assertEqual(v('走る', True, True, False), 'はしっていました')
    self.assertEqual(v('走る', True, False, True), '走っていませんでした')
    self.assertEqual(v('走る', True, False, False), 'はしっていませんでした')
    # Plain
    self.assertEqual(v('思い出す', False, True, True), '思い出していた')
    self.assertEqual(v('思い出す', False, True, False), 'おもいだしていた')
    self.assertEqual(v('思い出す', False, False, True), '思い出していなかった')
    self.assertEqual(v('思い出す', False, False, False), 'おもいだしていなかった')

  def test_provisional(self):
    def v(verb, positive, kanji):
      return VERB_HASH[verb].provisional(positive, kanji)
    # Positive
    self.assertEqual(v('知る', True, True), '知れば')
    self.assertEqual(v('知る', True, False), 'しれば')
    # Negative
    self.assertEqual(v('見せる', False, True), '見せなければ')
    self.assertEqual(v('見せる', False, False), 'みせなければ')
    # Once more, for good measure,
    # Positive
    self.assertEqual(v('学ぶ', True, True), '学べば')
    self.assertEqual(v('学ぶ', True, False), 'まなべば')
    # Negative
    self.assertEqual(v('待つ', False, True), '待たなければ')
    self.assertEqual(v('待つ', False, False), 'またなければ')

  def test_conditional(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].conditional(polite, positive, kanji)
    # Polite
    self.assertEqual(v('上がる', True, True, True), '上がりましたら')
    self.assertEqual(v('上がる', True, True, False), 'あがりましたら')
    self.assertEqual(v('泣く', True, False, True), '泣きませんでしたら')
    self.assertEqual(v('泣く', True, False, False), 'なきませんでしたら')
    # Plain
    self.assertEqual(v('見える', False, True, True), '見えたら')
    self.assertEqual(v('見える', False, True, False), 'みえたら')
    self.assertEqual(v('飲む', False, False, True), '飲まなかったら')
    self.assertEqual(v('飲む', False, False, False), 'のまなかったら')

  def test_potential(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].potential(polite, positive, kanji)
    # Ichidan (as it has ~rare~),
    # Polite
    self.assertEqual(v('開ける', True, True, True), '開けられます')
    self.assertEqual(v('開ける', True, True, False), 'あけられます')
    self.assertEqual(v('上げる', True, False, True), '上げられません')
    self.assertEqual(v('上げる', True, False, False), 'あげられません')
    # Plain
    self.assertEqual(v('浴びる', False, True, True), '浴びられる')
    self.assertEqual(v('浴びる', False, True, False), 'あびられる')
    self.assertEqual(v('決める', False, False, True), '決められない')
    self.assertEqual(v('決める', False, False, False), 'きめられない')
    # Godan,
    # Polite
    self.assertEqual(v('打つ', True, True, True), '打てます')
    self.assertEqual(v('打つ', True, True, False), 'うてます')
    self.assertEqual(v('泣く', True, False, True), '泣けません')
    self.assertEqual(v('泣く', True, False, False), 'なけません')
    # Plain
    self.assertEqual(v('思う', False, True, True), '思える')
    self.assertEqual(v('思う', False, True, False), 'おもえる')
    self.assertEqual(v('飲む', False, False, True), '飲めない')
    self.assertEqual(v('飲む', False, False, False), 'のめない')

  def test_causative(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].causative(polite, positive, kanji)
    # Ichidan (as it has ~saseru~),
    # Polite
    self.assertEqual(v('開ける', True, True, True), '開けさせます')
    self.assertEqual(v('開ける', True, True, False), 'あけさせます')
    self.assertEqual(v('上げる', True, False, True), '上げさせません')
    self.assertEqual(v('上げる', True, False, False), 'あげさせません')
    # Plain
    self.assertEqual(v('浴びる', False, True, True), '浴びさせる')
    self.assertEqual(v('浴びる', False, True, False), 'あびさせる')
    self.assertEqual(v('決める', False, False, True), '決めさせない')
    self.assertEqual(v('決める', False, False, False), 'きめさせない')
    # Godan,
    # Polite
    self.assertEqual(v('打つ', True, True, True), '打たせます')
    self.assertEqual(v('打つ', True, True, False), 'うたせます')
    self.assertEqual(v('泣く', True, False, True), '泣かせません')
    self.assertEqual(v('泣く', True, False, False), 'なかせません')
    # Plain
    self.assertEqual(v('思う', False, True, True), '思わせる')
    self.assertEqual(v('思う', False, True, False), 'おもわせる')
    self.assertEqual(v('飲む', False, False, True), '飲ませない')
    self.assertEqual(v('飲む', False, False, False), 'のませない')

  def test_passive(self):
    def v(verb, polite, positive, kanji):
      return VERB_HASH[verb].passive(polite, positive, kanji)
    # Ichidan (as it has ~saseru~),
    # Polite
    self.assertEqual(v('開ける', True, True, True), '開けられます')
    self.assertEqual(v('開ける', True, True, False), 'あけられます')
    self.assertEqual(v('上げる', True, False, True), '上げられません')
    self.assertEqual(v('上げる', True, False, False), 'あげられません')
    # Plain
    self.assertEqual(v('浴びる', False, True, True), '浴びられる')
    self.assertEqual(v('浴びる', False, True, False), 'あびられる')
    self.assertEqual(v('決める', False, False, True), '決められない')
    self.assertEqual(v('決める', False, False, False), 'きめられない')
    # Godan,
    # Polite
    self.assertEqual(v('打つ', True, True, True), '打たれます')
    self.assertEqual(v('打つ', True, True, False), 'うたれます')
    self.assertEqual(v('泣く', True, False, True), '泣かれません')
    self.assertEqual(v('泣く', True, False, False), 'なかれません')
    # Plain
    self.assertEqual(v('思う', False, True, True), '思われる')
    self.assertEqual(v('思う', False, True, False), 'おもわれる')
    self.assertEqual(v('飲む', False, False, True), '飲まれない')
    self.assertEqual(v('飲む', False, False, False), 'のまれない')

def french_verb(**french):
  """A verb with only the data the French builders need."""
  return Verb({
    'kanji': '歩く', 'kana': 'あるく', 'verb-type': 'godan-ku', 'english': 'to walk',
    'french-conjugated': french,
  })

MARCHER = french_verb(infinitif='marcher', present='marche', participe='marché',
    auxiliaire='avoir', imperatif='marche', nous='marchons')
AIMER = french_verb(infinitif='aimer', present='aime', participe='aimé',
    auxiliaire='avoir', imperatif='aime', nous='aimons')
ALLER_ENSEMBLE = french_verb(infinitif='aller', present='va', participe='allé',
    auxiliaire='être', imperatif='va', nous='allons', complement='ensemble')
SE_LEVER = french_verb(infinitif='lever', present='lève', participe='levé',
    auxiliaire='avoir', imperatif='lève', nous='levons', pronominal=True)
S_HABILLER = french_verb(infinitif='habiller', present='habille', participe='habillé',
    auxiliaire='avoir', imperatif='habille', nous='habillons', pronominal=True)
HURLER = french_verb(infinitif='hurler', present='hurle', participe='hurlé',
    auxiliaire='avoir', imperatif='hurle', nous='hurlons')
ETRE_LA = french_verb(infinitif='être', present='est', participe='été',
    auxiliaire='avoir', imperatif='sois', nous='soyons', complement='là')

class TestFrenchVerbConjugation(unittest.TestCase):

  def test_elide(self):
    self.assertEqual(elide('ne', 'aime'), "n'aime")
    self.assertEqual(elide('ne', 'marche'), 'ne marche')
    self.assertEqual(elide('se', 'habiller'), "s'habiller")
    self.assertEqual(elide('ne', 'hurle'), 'ne hurle') # h aspiré
    self.assertEqual(elide('de', 'être'), "d'être")

  def test_french_present_indicative(self):
    self.assertEqual(MARCHER.french_present_indicative(True), 'marche')
    self.assertEqual(MARCHER.french_present_indicative(False), 'ne marche pas')
    self.assertEqual(AIMER.french_present_indicative(False), "n'aime pas")
    self.assertEqual(HURLER.french_present_indicative(False), 'ne hurle pas')
    self.assertEqual(ALLER_ENSEMBLE.french_present_indicative(False), 'ne va pas ensemble')
    self.assertEqual(SE_LEVER.french_present_indicative(True), 'se lève')
    self.assertEqual(SE_LEVER.french_present_indicative(False), 'ne se lève pas')
    self.assertEqual(S_HABILLER.french_present_indicative(False), "ne s'habille pas")

  def test_french_presumptive(self):
    self.assertEqual(MARCHER.french_presumptive(True), 'va sans doute marcher')
    self.assertEqual(MARCHER.french_presumptive(False), 'ne va sans doute pas marcher')
    self.assertEqual(S_HABILLER.french_presumptive(True), "va sans doute s'habiller")

  def test_french_volitional(self):
    self.assertEqual(MARCHER.french_volitional(), 'marchons !')
    self.assertEqual(ALLER_ENSEMBLE.french_volitional(), 'allons ensemble !')
    self.assertEqual(SE_LEVER.french_volitional(), 'levons-nous !')

  def test_french_imperative(self):
    self.assertEqual(MARCHER.french_imperative(True), 'marche !')
    self.assertEqual(AIMER.french_imperative(False), "n'aime pas !")
    self.assertEqual(SE_LEVER.french_imperative(True), 'lève-toi !')
    self.assertEqual(SE_LEVER.french_imperative(False), 'ne te lève pas !')
    self.assertEqual(S_HABILLER.french_imperative(False), "ne t'habille pas !")

  def test_french_past_indicative(self):
    self.assertEqual(MARCHER.french_past_indicative(True), 'a marché')
    self.assertEqual(MARCHER.french_past_indicative(False), "n'a pas marché")
    self.assertEqual(ALLER_ENSEMBLE.french_past_indicative(True), 'est allé ensemble')
    self.assertEqual(SE_LEVER.french_past_indicative(True), "s'est levé")
    self.assertEqual(SE_LEVER.french_past_indicative(False), "ne s'est pas levé")

  def test_french_past_presumptive(self):
    self.assertEqual(MARCHER.french_past_presumptive(True), 'a sans doute marché')
    self.assertEqual(MARCHER.french_past_presumptive(False), "n'a sans doute pas marché")
    self.assertEqual(SE_LEVER.french_past_presumptive(False), "ne s'est sans doute pas levé")

  def test_french_progressive(self):
    self.assertEqual(MARCHER.french_present_progressive(True), 'est en train de marcher')
    self.assertEqual(AIMER.french_present_progressive(False), "n'est pas en train d'aimer")
    self.assertEqual(SE_LEVER.french_past_progressive(True), 'était en train de se lever')
    self.assertEqual(MARCHER.french_past_progressive(False), "n'était pas en train de marcher")

  def test_french_conditionals(self):
    self.assertEqual(MARCHER.french_provisional(True), 'si on marche')
    self.assertEqual(AIMER.french_conditional(False), "si on n'aime pas")
    self.assertEqual(SE_LEVER.french_conditional(True), 'si on se lève')

  def test_french_potential(self):
    self.assertEqual(MARCHER.french_potential(True), 'peut marcher')
    self.assertEqual(SE_LEVER.french_potential(False), 'ne peut pas se lever')

  def test_french_causative(self):
    self.assertEqual(MARCHER.french_causative(True), 'faire marcher')
    self.assertEqual(MARCHER.french_causative(False), 'ne pas faire marcher')
    self.assertEqual(SE_LEVER.french_causative(True), 'faire lever')
    self.assertEqual(ETRE_LA.french_causative(True), 'obliger à être là')

  def test_french_passive(self):
    self.assertEqual(AIMER.french_passive(True), 'être aimé')
    self.assertEqual(AIMER.french_passive(False), 'ne pas être aimé')
    self.assertEqual(ETRE_LA.french_passive(True), "subir le fait d'être là")

class TestAllJapaneseVerbConjugation(unittest.TestCase):

  def test_all_vocab_can_be_generated(self):
    verbs = VERB_HASH.values()
    for verb in verbs:
      for i in range(8):
        polite = i//4 % 2 == 0
        positive = i//2 % 2 == 0
        kanji = i % 2 == 0

        self.assertIsInstance(verb.present_indicative(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.presumptive(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.imperative(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.past_indicative(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.past_presumptive(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.present_progressive(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.past_progressive(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.conditional(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.potential(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.causative(polite=polite, positive=positive, kanji=kanji), str)
        self.assertIsInstance(verb.passive(polite=polite, positive=positive, kanji=kanji), str)

      for i in range(4):
        polite = i//2 % 2 == 0
        positive = polite
        kanji = i % 2 == 0

        self.assertIsInstance(verb.volitional(polite=polite, kanji=kanji), str)
        self.assertIsInstance(verb.provisional(positive=positive, kanji=kanji), str)

  def test_all_vocab_has_french(self):
    for verb in VERB_HASH.values():
      for conjugation in CONJUGATIONS:
        method = getattr(verb, 'french_' + conjugation.conjugation_name())
        forms = [method(positive=True), method(positive=False)] if conjugation.has_negative else [method()]
        for form in forms:
          self.assertIsInstance(form, str)
          self.assertNotIn('~', form)

class TestConjugator(unittest.TestCase):

  def test_field_ordering(self):
    c = Conjugation('Present Indicative', 'Présent')
    self.assertListEqual(c.field_names(), [
        'present_indicative_french_positive',
        'present_indicative_french_negative',
        'present_indicative_plain_positive_kanji',
        'present_indicative_plain_positive_kana',
        'present_indicative_plain_negative_kanji',
        'present_indicative_plain_negative_kana',
        'present_indicative_polite_positive_kanji',
        'present_indicative_polite_positive_kana',
        'present_indicative_polite_negative_kanji',
        'present_indicative_polite_negative_kana',
      ])

    c = Conjugation('Volitional', 'Volitif', has_negative=False)
    self.assertListEqual(c.field_names(), [
        'volitional_french_positive',
        'volitional_plain_positive_kanji',
        'volitional_plain_positive_kana',
        'volitional_polite_positive_kanji',
        'volitional_polite_positive_kana',
      ])

    c = Conjugation('Provisional', 'Conditionnel en ～ば', has_polite=False)
    self.assertListEqual(c.field_names(), [
        'provisional_french_positive',
        'provisional_french_negative',
        'provisional_plain_positive_kanji',
        'provisional_plain_positive_kana',
        'provisional_plain_negative_kanji',
        'provisional_plain_negative_kana',
      ])

    c = Conjugation('Fake Verb Form', 'Faux', has_polite=False, has_negative=False)
    self.assertListEqual(c.field_names(), [
        'fake_verb_form_french_positive',
        'fake_verb_form_plain_positive_kanji',
        'fake_verb_form_plain_positive_kana',
      ])

  def test_field_mapping(self):
    c = Conjugation('Present Indicative', 'Présent')
    self.assertListEqual(c.map_verb_fields(VERB_HASH['歩く']), [
        'marche',
        'ne marche pas',
        '歩く',
        'あるく',
        '歩かない',
        'あるかない',
        '歩きます',
        'あるきます',
        '歩きません',
        'あるきません',
      ])

    c = Conjugation('Volitional', 'Volitif', has_negative=False)
    self.assertListEqual(c.map_verb_fields(VERB_HASH['信じる']), [
        'croyons !',
        '信じよう',
        'しんじよう',
        '信じましょう',
        'しんじましょう',
      ])

    c = Conjugation('Provisional', 'Conditionnel en ～ば', has_polite=False)
    self.assertListEqual(c.map_verb_fields(VERB_HASH['合う']), [
        'si on va ensemble',
        'si on ne va pas ensemble',
        '合えば',
        'あえば',
        '合わなければ',
        'あわなければ',
      ])

  def test_all_verbs_can_conjugate(self):
    tested_cases = 0
    for conjugation in CONJUGATIONS:
      for verb in VERB_HASH.values():
        self.assertGreater(len(conjugation.map_verb_fields(verb)), 0)
        tested_cases += 1

    self.assertGreater(tested_cases, 200)
