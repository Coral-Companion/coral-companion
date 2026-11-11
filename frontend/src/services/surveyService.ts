import type { Survey } from '../types/survey'

async function getAll(): Promise<Survey[]> {
    const apiBase = import.meta.env.VITE_API_BASE as string
    const url = apiBase ? `${apiBase}/api/surveys` : '/api/surveys'
    const res = await fetch(url, { method: 'GET' })
    if (!res.ok) throw new Error('Segmentation request failed.')
    return await res.json();
}

async function create(survey: Survey): Promise<Survey> {
    console.log("creating survey");
    console.log(survey);
    const apiBase = import.meta.env.VITE_API_BASE as string
    const url = apiBase ? `${apiBase}/api/surveys` : '/api/surveys'
    const res = await fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            "name": survey.name,
            "timestamp": survey.timestamp,
            "diveSite": survey.diveSite
        }),
        headers: {
            "Content-Type": "application/json",
        }
    })
    if (!res.ok) throw new Error('Session creation request failed.')
    await res.json().then(response => { survey.id = response.sessionId });
    return survey;
}

export default { getAll, create }
