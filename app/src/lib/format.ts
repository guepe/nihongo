const MINUTE = 60 * 1000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

/** '< 1 min', '10 min', '3 h', '4 j', '2,5 mois', '1,2 an' */
export function formatInterval(ms: number): string {
  const round = (n: number) => n.toLocaleString('fr-FR', { maximumFractionDigits: n < 10 ? 1 : 0 })
  if (ms < MINUTE) return '< 1 min'
  if (ms < HOUR) return `${Math.round(ms / MINUTE)} min`
  if (ms < DAY) return `${Math.round(ms / HOUR)} h`
  if (ms < 30 * DAY) return `${Math.round(ms / DAY)} j`
  if (ms < 365 * DAY) return `${round(ms / (30 * DAY))} mois`
  const years = ms / (365 * DAY)
  return `${round(years)} an${years >= 2 ? 's' : ''}`
}

export const LEVEL_LABELS: Record<string, string> = {
  n5: 'N5', n4: 'N4', n3: 'N3', n2: 'N2', n1: 'N1', none: 'Sans niveau',
}
