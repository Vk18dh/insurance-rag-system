import { Analytics } from "@vercel/analytics/next"
import type { Metadata, Viewport } from "next"
import { Inter, Geist_Mono } from "next/font/google"
import { AuthProvider } from "@/components/auth-provider"
import { InteractiveBackground } from "@/components/interactive-background"
import AIBotWrapper from "@/components/3d/ai-bot-wrapper"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" })

export const metadata: Metadata = {
  title: "InsuraLens — Grounded Policy Intelligence",
  description:
    "Query regulatory policies and insurance rules with guaranteed citations. AI-generated answers grounded in source documents with confidence scoring and safety checks.",
  generator: "v0.app",
  icons: {
    icon: [
      { url: "/icon-light-32x32.png", media: "(prefers-color-scheme: light)" },
      { url: "/icon-dark-32x32.png", media: "(prefers-color-scheme: dark)" },
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: "/apple-icon.png",
  },
}

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#111524" },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`dark bg-background ${inter.variable} ${geistMono.variable}`}>
      <body className="font-sans antialiased">
        <AuthProvider>
          <InteractiveBackground>
            {children}
            <AIBotWrapper />
          </InteractiveBackground>
        </AuthProvider>
        {process.env.NODE_ENV === "production" && <Analytics />}
      </body>
    </html>
  )
}
