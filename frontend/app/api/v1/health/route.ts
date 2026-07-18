import { NextResponse } from "next/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function GET() {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5_000)
    const upstream = await fetch(`${API_URL}/api/v1/health`, {
      signal: controller.signal,
      cache: "no-store",
    })
    clearTimeout(timeout)

    if (upstream.ok) {
      const data = await upstream.json()
      return NextResponse.json({ ...data, live: true })
    }
  } catch {
    // fall through
  }

  return NextResponse.json({ status: "demo", version: "demo", components: {}, live: false })
}
