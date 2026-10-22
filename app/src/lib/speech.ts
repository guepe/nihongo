// Reads Japanese aloud with the voices of the device (Kyoko, O-Ren… on Apple devices).

let voice: SpeechSynthesisVoice | null | undefined

function japaneseVoice(): SpeechSynthesisVoice | null {
  if (voice !== undefined) return voice
  const voices = speechSynthesis.getVoices().filter((v) => v.lang.replace('_', '-').startsWith('ja'))
  if (!voices.length) return null // the list may not be loaded yet: try again next time
  // Prefer the higher-quality voices when the device has them.
  voice = voices.find((v) => /premium|enhanced|amélioré/i.test(v.name))
    ?? voices.find((v) => v.localService)
    ?? voices[0]
  return voice
}

export function canSpeak(): boolean {
  return typeof speechSynthesis !== 'undefined'
}

/** 'まいつき / まいげつ' → 'まいつき、まいげつ' ; '～はい' → 'はい' */
export function speakable(kana: string): string {
  return kana.replace(/[～~]/g, '').replace(/\s*\/\s*/g, '、').replace(/[()（）]/g, '、').trim()
}

/** Must first be called from a tap or a key press: iOS refuses speech otherwise. */
export function speak(kana: string): void {
  if (!canSpeak()) return
  speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(speakable(kana))
  utterance.lang = 'ja-JP'
  utterance.rate = 0.9
  const v = japaneseVoice()
  if (v) utterance.voice = v
  speechSynthesis.speak(utterance)
}

export function stopSpeaking(): void {
  if (canSpeak()) speechSynthesis.cancel()
}
