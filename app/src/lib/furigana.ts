// Splits a word into parts with and without furigana: kana written in the word itself
// (okurigana, prefixes) gets no reading above it.
// 食べる / たべる → [食 (た)] べる ; お茶 / おちゃ → お [茶 (ちゃ)]

export interface Segment {
  text: string
  reading?: string // kana shown above the text
}

const isKana = (c: string) => /[぀-ヿ]/.test(c)

export function furigana(word: string, kana: string): Segment[] {
  // Several readings, or a word written in kana only: nothing to put above.
  if (word === kana || /[\/（(～~]/.test(kana) || !/[一-鿿々]/.test(word)) {
    return [{ text: word }]
  }
  let start = 0
  while (start < word.length && start < kana.length && word[start] === kana[start] && isKana(word[start])) {
    start++
  }
  let end = 0
  while (end < word.length - start && end < kana.length - start
    && word[word.length - 1 - end] === kana[kana.length - 1 - end] && isKana(word[word.length - 1 - end])) {
    end++
  }
  const middle = word.slice(start, word.length - end)
  const reading = kana.slice(start, kana.length - end)
  if (!middle || !reading) return [{ text: word }]
  const segments: Segment[] = []
  if (start) segments.push({ text: word.slice(0, start) })
  segments.push({ text: middle, reading })
  if (end) segments.push({ text: word.slice(word.length - end) })
  return segments
}
