import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Sidebar } from '@/components/chat/sidebar'
import { AuthProvider } from '@/components/auth-provider'
import { SiteHeader } from '@/components/site-header'

// Mock the Next.js router and useParams
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
  usePathname: vi.fn(() => '/'),
  useParams: vi.fn(() => ({ id: undefined })),
}))

vi.mock('@/lib/api-client', async () => {
  const actual = await vi.importActual('@/lib/api-client')
  return {
    ...actual as any,
    apiClient: {
      getConversations: vi.fn().mockResolvedValue([]),
    },
    getToken: vi.fn().mockReturnValue('mock-token'),
  }
})

describe('Separation of Concerns', () => {
  it('does not contain expert or admin links in Sidebar', () => {
    render(
      <AuthProvider>
        <Sidebar />
      </AuthProvider>
    )
    
    // Check what links/buttons exist
    const buttons = screen.getAllByRole('button')
    const buttonTexts = buttons.map(b => b.textContent)
    
    expect(buttonTexts).not.toContain('Expert')
    expect(buttonTexts).not.toContain('Admin')
    expect(buttonTexts).not.toContain('Management')
  })

  it('does not contain expert or admin links in SiteHeader', () => {
    render(<SiteHeader />)
    
    const textContent = document.body.textContent || ''
    expect(textContent).not.toContain('Expert')
    expect(textContent).not.toContain('Admin')
    expect(textContent).not.toContain('Management')
  })
})
