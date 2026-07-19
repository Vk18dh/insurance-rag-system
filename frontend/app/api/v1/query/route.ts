import { NextResponse } from "next/server"
import { buildDemoResponse } from "@/lib/demo-data"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function POST(request: Request) {
  let query = ""
  try {
    const body = await request.json()
    query = typeof body?.query === "string" ? body.query : ""
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 })
  }

  if (!query.trim()) {
    return NextResponse.json({ error: "Query is required" }, { status: 400 })
  }

  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 120_000)

    const upstream = await fetch(`${API_URL}/api/v1/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      signal: controller.signal,
      cache: "no-store",
    })
    clearTimeout(timeout)

    if (upstream.ok) {
      const data = await upstream.json()
      return NextResponse.json(data)
    } else {
      const errBody = await upstream.text()
      return NextResponse.json(
        { error: `Backend returned ${upstream.status}: ${errBody}` },
        { status: upstream.status }
      )
    }
  } catch (err: any) {
    return NextResponse.json(
      { error: `Backend unreachable: ${err.message}` },
      { status: 503 }
    )
  }
}
