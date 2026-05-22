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
import ForumZoneListPage from './pages/ForumZoneListPage'
import ForumPostListPage from './pages/ForumPostListPage'
import ForumPostDetailPage from './pages/ForumPostDetailPage'
import AIChatPage from './pages/AIChatPage'

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
        path="/forums"
        element={
          <AuthGuard>
            <ForumZoneListPage />
          </AuthGuard>
        }
      />
      <Route
        path="/forums/z/:slug"
        element={
          <AuthGuard>
            <ForumPostListPage />
          </AuthGuard>
        }
      />
      <Route
        path="/forums/p/:postId"
        element={
          <AuthGuard>
            <ForumPostDetailPage />
          </AuthGuard>
        }
      />
      <Route
        path="/ai-chat"
        element={
          <AuthGuard>
            <AIChatPage />
          </AuthGuard>
        }
      />
      <Route
        path="/admin/*"
        element={
          <AuthGuard requireAdmin>
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
