import type { IdentifyApiResponse } from '../types/api'
import type { Segment } from '../types/segment'
import type { ObservationSummary } from "../types/observationSummary";

const apiBase = import.meta.env.VITE_API_BASE as string

async function identifyCoralBySegments(selectedSegments: Segment[], file: File): Promise<IdentifyApiResponse> {
  const url = apiBase ? `${apiBase}/api/identify-by-segments` : '/api/identify-by-segments'
  const form = new FormData()
  form.append('image', file)
  form.append('segments', JSON.stringify({ selectedSegments }))
  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Identify request failed.')
  return await res.json()
}

interface ConfirmCoralRequest {
  image: File
  selectedSegments: Segment[]
  selectedCandidateId: string | null
  diveSite: string
  coralName: string
  surveyId: string
}

async function confirmCoral(request: ConfirmCoralRequest): Promise<void> {
  const url = apiBase ? `${apiBase}/api/confirm-coral` : '/api/confirm-coral'
  const form = new FormData()
  form.append('image', request.image)
  form.append('segments', JSON.stringify({ selectedSegments: request.selectedSegments }))
  form.append('selectedCandidateId', request.selectedCandidateId ?? '')
  form.append('diveSite', request.diveSite)
  form.append('coralName', request.coralName)
  form.append('surveyId', request.surveyId)
  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Confirmation request failed.')
  return res.json()
}
async function getObservationSummaries(): Promise<ObservationSummary[]> {
    const url = apiBase ? `${apiBase}/api/observation-summaries` : '/api/observation-summaries'
    const res = await fetch(url, { method: 'GET' })
    if (!res.ok) throw new Error('Observation summaries request failed.')
    return await res.json();
}


export default { identifyCoralBySegments, confirmCoral, getObservationSummaries }
