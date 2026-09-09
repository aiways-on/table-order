import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from './LoginPage.jsx'
import { AuthProvider } from '../auth/AuthContext.jsx'

// Mock the router navigate so we can assert redirect-on-success.
const navigate = vi.fn()
vi.mock('react-router-dom', async (orig) => ({
  ...(await orig()),
  useNavigate: () => navigate,
}))

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear()
    navigate.mockClear()
    global.fetch = vi.fn()
  })
  afterEach(() => vi.restoreAllMocks())

  it('disables submit until store_code, username and 8+ char password are present (BR-FA01)', () => {
    renderLogin()
    const btn = screen.getByRole('button', { name: '로그인' })
    expect(btn).toBeDisabled()

    fireEvent.change(screen.getByLabelText('매장 식별자'), { target: { value: 'cafe1' } })
    fireEvent.change(screen.getByLabelText('사용자명'), { target: { value: 'owner' } })
    fireEvent.change(screen.getByLabelText(/비밀번호/), { target: { value: 'short' } })
    expect(btn).toBeDisabled()

    fireEvent.change(screen.getByLabelText(/비밀번호/), { target: { value: 'longenough' } })
    expect(btn).toBeEnabled()
  })

  it('logs in, persists store_id and redirects to /dashboard (BR-FA02)', async () => {
    global.fetch.mockResolvedValue(
      new Response(JSON.stringify({ store_id: 'store-123', role: 'admin' }), { status: 200 }),
    )
    renderLogin()
    fireEvent.change(screen.getByLabelText('매장 식별자'), { target: { value: 'cafe1' } })
    fireEvent.change(screen.getByLabelText('사용자명'), { target: { value: 'owner' } })
    fireEvent.change(screen.getByLabelText(/비밀번호/), { target: { value: 'longenough' } })
    fireEvent.click(screen.getByRole('button', { name: '로그인' }))

    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/dashboard', { replace: true }))
    expect(JSON.parse(localStorage.getItem('admin_store'))).toMatchObject({ store_id: 'store-123' })
  })

  it('surfaces the server error message on failure (BR-FA04)', async () => {
    global.fetch.mockResolvedValue(
      new Response(JSON.stringify({ detail: '로그인 시도가 너무 많습니다' }), { status: 429 }),
    )
    renderLogin()
    fireEvent.change(screen.getByLabelText('매장 식별자'), { target: { value: 'cafe1' } })
    fireEvent.change(screen.getByLabelText('사용자명'), { target: { value: 'owner' } })
    fireEvent.change(screen.getByLabelText(/비밀번호/), { target: { value: 'longenough' } })
    fireEvent.click(screen.getByRole('button', { name: '로그인' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('로그인 시도가 너무 많습니다')
    expect(navigate).not.toHaveBeenCalledWith('/dashboard', { replace: true })
  })
})
