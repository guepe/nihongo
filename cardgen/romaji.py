"""
Convert kana to Hepburn romaji, eg. 'がっこう' -> 'gakkou'.

Long vowels are spelled as in kana (おう -> ou, ー repeats the vowel: コーヒー -> koohii)
rather than with macrons, so the romaji maps back to the kana letter by letter.
Characters that aren't kana (spaces, '/', '～', ...) are kept as is.
"""

import re

# Two-kana combinations first; they're matched before single kana.
DIGRAPHS = {
  'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
  'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
  'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho', 'しぇ': 'she',
  'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo', 'じぇ': 'je',
  'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho', 'ちぇ': 'che',
  'ぢゃ': 'ja', 'ぢゅ': 'ju', 'ぢょ': 'jo',
  'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
  'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
  'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
  'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
  'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
  'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
  # Loanword spellings (katakana is converted to hiragana first).
  'てぃ': 'ti', 'でぃ': 'di', 'とぅ': 'tu', 'どぅ': 'du', 'でゅ': 'dyu',
  'ふぁ': 'fa', 'ふぃ': 'fi', 'ふぇ': 'fe', 'ふぉ': 'fo', 'ふゅ': 'fyu',
  'うぃ': 'wi', 'うぇ': 'we', 'うぉ': 'wo',
  'ゔぁ': 'va', 'ゔぃ': 'vi', 'ゔぇ': 've', 'ゔぉ': 'vo',
  'つぁ': 'tsa', 'つぃ': 'tsi', 'つぇ': 'tse', 'つぉ': 'tso',
  'いぇ': 'ye',
}

MONOGRAPHS = {
  'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
  'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
  'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
  'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
  'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
  'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
  'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
  'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
  'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
  'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
  'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
  'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
  'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
  'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
  'わ': 'wa', 'ゐ': 'i', 'ゑ': 'e', 'を': 'o',
  'ゔ': 'vu',
  # Small kana on their own (eg. after another vowel in loanwords).
  'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o',
  'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo', 'ゎ': 'wa',
  # Punctuation
  '、': ', ', '。': '. ', '（': ' (', '）': ')', '・': ' ',
}

# Words where は is the particle 'wa', not 'ha'.
PARTICLE_WA = {
  'あるいは', 'こんにちは', 'こんばんは', 'じつは', 'それでは', 'では', 'または',
}

def katakana_to_hiragana(text):
  return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in text)

def to_romaji(kana):
  """to_romaji('がっこう') -> 'gakkou'; to_romaji('コーヒー') -> 'koohii'."""
  # Readings like 'まいつき / まいげつ' are converted part by part.
  parts = re.split(r'(\s*/\s*)', kana)
  return ''.join(part if '/' in part else _convert(part) for part in parts)

def _convert(kana):
  text = katakana_to_hiragana(kana)
  syllables = []
  i = 0
  while i < len(text):
    pair = text[i:i+2]
    if pair in DIGRAPHS:
      syllables.append(DIGRAPHS[pair])
      i += 2
    else:
      syllables.append(MONOGRAPHS.get(text[i], text[i]))
      i += 1

  if text in PARTICLE_WA:
    syllables[-1] = 'wa'

  result = ''
  for n, syllable in enumerate(syllables):
    following = syllables[n+1] if n + 1 < len(syllables) else ''
    if syllable == 'っ':
      # Double the next consonant: がっこう -> gakkou, まっちゃ -> matcha.
      if following.startswith('ch'):
        result += 't'
      elif following[:1].isalpha() and following[:1] not in 'aeiou':
        result += following[0]
    elif syllable == 'ん':
      # Apostrophe avoids ambiguity: きんえん -> kin'en (not ki-nen).
      result += "n'" if following[:1] in ('a', 'i', 'u', 'e', 'o', 'y') else 'n'
    elif syllable == 'ー':
      # Long vowel mark repeats the previous vowel: コーヒー -> koohii.
      vowels = [c for c in result if c in 'aeiou']
      result += vowels[-1] if vowels else ''
    else:
      result += syllable
  return result
