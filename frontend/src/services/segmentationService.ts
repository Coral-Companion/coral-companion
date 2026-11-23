import { CoralCandidate } from '@/types/api';
import type { Segment } from '../types/segment'

export interface SegmentResponse {
  segmentationId: string
  // TODO: are image dimensions required at all?
  image: { width: number; height: number }
  segments: Segment[]
  observationCandidates: [CoralCandidate]
}

async function segmentImage(file: File, layers: number = 0): Promise<SegmentResponse> {
  const form = new FormData()
  form.append('image', file)
  form.append('layers', String(layers))
  const apiBase = import.meta.env.VITE_API_BASE as string
  const url = apiBase ? `${apiBase}/api/upload-coral-image` : '/api/upload-coral-image'

  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Segmentation request failed.')
  return await res.json()
}

export default { segmentImage }
