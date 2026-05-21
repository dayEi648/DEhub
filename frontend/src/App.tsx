import { Routes, Route } from 'react-router-dom'
import AuthGuard from './components/AuthGuard'
import AdminLayout from './components/AdminLayout'
import AdminDashboard from './pages/admin/AdminDashboard'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import HomePage from './pages/HomePage'
import ProfilePage from './pages/ProfilePage'
import BlogListPage from './pages/BlogListPage'
import BlogDetailPage from './pages/BlogDetailPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <AuthGuard>
            <HomePage />
          </AuthGuard>
        }
      />
      <Route
        path="/profile"
        element={
          <AuthGuard>
            <ProfilePage />
          </AuthGuard>
        }
      />
      <Route
        path="/blogs"
        element={
          <AuthGuard>
            <BlogListPage />
          </AuthGuard>
        }
      />
      <Route
        path="/blogs/:slug"
        element={
          <AuthGuard>
            <BlogDetailPage />
          </AuthGuard>
        }
      />
      <Route
        path="/admin/*"
        element={
          <AuthGuard>
            <AdminLayout>
              <AdminDashboard />
            </AdminLayout>
          </AuthGuard>
        }
      />
    </Routes>
  )
}

export default App
