import { trackApiCall } from '../utils/performance'

const COMMENTARY_API_URL =
  (import.meta as any).env?.VITE_COMMENTARY_API_URL || 'http://localhost:5050/commentary'

export type MoveCommentaryRequest = {
  fen: string | null
  move: string
}

export type MoveCommentaryResponse = {
  commentary?: string
  summary?: string
  plan?: string
  fen?: string | null
  move?: string
}

export const commentaryApi = {
  async getMoveCommentary(
    payload: MoveCommentaryRequest,
    signal?: AbortSignal,
  ): Promise<MoveCommentaryResponse> {
    return trackApiCall(async () => {
      const response = await fetch(COMMENTARY_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal,
      })

      if (!response.ok) {
        const errorText = await response.text().catch(() => '')
        throw new Error(`Commentary request failed (${response.status}): ${errorText}`)
      }

      return response.json()
    }, 'POST /commentary')
  },
}

