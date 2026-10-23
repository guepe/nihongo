// Reads Japanese aloud with the voices of the device (Kyoko, O-Ren… on Apple devices).
//
// Two iOS pitfalls: the voice is never forced (iOS lists "enhanced" voices that aren't
// downloaded, and choosing one gives silence: with only the language set, the device uses
// the voice chosen in its settings), and speak() never directly follows cancel() (Safari
// then drops the new utterance).

export function canSpeak(): boolean {
  return typeof speechSynthesis !== 'undefined'
}

/** 'まいつき / まいげつ' → 'まいつき、まいげつ' ; '～はい' → 'はい' */
export function speakable(kana: string): string {
  return kana.replace(/[～~]/g, '').replace(/\s*\/\s*/g, '、').replace(/[()（）]/g, '、').trim()
}

export type SpeechOutcome = 'start' | 'end' | `error: ${string}`

function utterance(kana: string, onoutcome?: (outcome: SpeechOutcome) => void): SpeechSynthesisUtterance {
  const u = new SpeechSynthesisUtterance(speakable(kana))
  u.lang = 'ja-JP'
  u.rate = 0.9
  if (onoutcome) {
    u.onstart = () => onoutcome('start')
    u.onend = () => onoutcome('end')
    u.onerror = (e) => onoutcome(`error: ${e.error}`)
  }
  return u
}

/** Must first be called from a tap or a key press: iOS refuses speech otherwise. */
export function speak(kana: string, onoutcome?: (outcome: SpeechOutcome) => void): void {
  if (!canSpeak()) return
  const u = utterance(kana, onoutcome)
  if (speechSynthesis.speaking || speechSynthesis.pending) {
    speechSynthesis.cancel()
    setTimeout(() => speechSynthesis.speak(u), 100)
  } else {
    speechSynthesis.speak(u)
  }
}

export function stopSpeaking(): void {
  if (canSpeak() && (speechSynthesis.speaking || speechSynthesis.pending)) speechSynthesis.cancel()
}

/** Japanese voices known to the device (the list may load a moment after the page). */
export function japaneseVoices(): Promise<SpeechSynthesisVoice[]> {
  const list = () => speechSynthesis.getVoices().filter((v) => v.lang.replace('_', '-').startsWith('ja'))
  if (!canSpeak()) return Promise.resolve([])
  if (speechSynthesis.getVoices().length) return Promise.resolve(list())
  return new Promise((resolve) => {
    const done = () => resolve(list())
    speechSynthesis.addEventListener('voiceschanged', done, { once: true })
    setTimeout(done, 1500)
  })
}
