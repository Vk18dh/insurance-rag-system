"use client"

import dynamic from "next/dynamic"

const AIBotScene = dynamic(() => import("./ai-bot-scene"), { ssr: false })

export default function AIBotWrapper() {
  return <AIBotScene />
}
