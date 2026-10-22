import { describe, expect, it } from 'vitest'

import { furigana } from './furigana'
import { speakable } from './speech'

describe('furigana', () => {
  it('leaves okurigana and kana prefixes without reading', () => {
    expect(furigana('食べる', 'たべる')).toEqual([{ text: '食', reading: 'た' }, { text: 'べる' }])
    expect(furigana('お茶', 'おちゃ')).toEqual([{ text: 'お' }, { text: '茶', reading: 'ちゃ' }])
    expect(furigana('学校', 'がっこう')).toEqual([{ text: '学校', reading: 'がっこう' }])
  })

  it('puts the whole reading over mixed words', () => {
    expect(furigana('取り消す', 'とりけす')).toEqual([{ text: '取り消', reading: 'とりけ' }, { text: 'す' }])
  })

  it('shows nothing above kana-only words or multiple readings', () => {
    expect(furigana('コーヒー', 'コーヒー')).toEqual([{ text: 'コーヒー' }])
    expect(furigana('何', 'なに / なん')).toEqual([{ text: '何' }])
  })
})

describe('speakable', () => {
  it('turns separators into pauses', () => {
    expect(speakable('まいつき / まいげつ')).toBe('まいつき、まいげつ')
    expect(speakable('～はい')).toBe('はい')
  })
})
