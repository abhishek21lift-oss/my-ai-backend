import { NextResponse } from 'next/server'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'
const CRON_SECRET = process.env.CRON_SECRET ?? ''

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/cron/daily-reports`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${CRON_SECRET}`,
        'Content-Type': 'application/json',
      },
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json({ error: 'Failed to trigger reports' }, { status: 500 })
  }
}
