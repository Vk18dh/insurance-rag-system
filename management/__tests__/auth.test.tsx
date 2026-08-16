import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import LoginPage from '@/app/login/page'
import { AuthProvider } from '@/components/auth-provider'
import { apiClient } from '@/lib/api-client'
import { useRouter } from 'next/navigation'

// Mock the Next.js router
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
  usePathname: vi.fn(() => '/login'),
}))

// Mock apiClient
vi.mock('@/lib/api-client', async () => {
  const actual = await vi.importActual('@/lib/api-client')
  return {
    ...actual as any,
    apiClient: {
      login: vi.fn(),
    },
    getToken: vi.fn(),
    setToken: vi.fn(),
  }
})

describe('Authentication', () => {
  it('renders login page correctly', () => {
    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    )
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument()
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
  })

  it('handles successful login', async () => {
    (apiClient.login as any).mockResolvedValue({ access_token: 'fake-token' })
    const mockRouter = { push: vi.fn() }
    ;(useRouter as any).mockReturnValue(mockRouter)

    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /Sign in/i }))

    await waitFor(() => {
      expect(apiClient.login).toHaveBeenCalledWith('testuser', 'password123')
      expect(mockRouter.push).toHaveBeenCalledWith('/')
    })
  })

  it('handles login failure', async () => {
    (apiClient.login as any).mockRejectedValue(new Error('Invalid credentials'))
    
    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'wrongpass' } })
    fireEvent.click(screen.getByRole('button', { name: /Sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })
})
