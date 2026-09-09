import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/AppLayout.jsx'
import SessionRoute from './components/SessionRoute.jsx'
import StartPage from './pages/StartPage.jsx'
import MenuPage from './pages/MenuPage.jsx'
import OrdersPage from './pages/OrdersPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/start" element={<StartPage />} />
      <Route
        element={
          <SessionRoute>
            <AppLayout />
          </SessionRoute>
        }
      >
        <Route path="/menu" element={<MenuPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/" element={<Navigate to="/menu" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/menu" replace />} />
    </Routes>
  )
}
