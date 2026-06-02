import { Routes, Route } from 'react-router-dom'
import AuthGuard from './components/AuthGuard'
import AdminLayout from './components/AdminLayout'
import ScrollProgress from './components/ui/ScrollProgress'
import BackToTop from './components/ui/BackToTop'
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
import PortfolioPage from './pages/PortfolioPage'
import AdminDashboard from './pages/admin/AdminDashboard'

function App() {
  return (
    <>
      <ScrollProgress />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<AuthGuard />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/blogs" element={<BlogListPage />} />
          <Route path="/blogs/:slug" element={<BlogDetailPage />} />
          <Route path="/forums" element={<ForumZoneListPage />} />
          <Route path="/forums/z/:slug" element={<ForumPostListPage />} />
          <Route path="/forums/p/:postId" element={<ForumPostDetailPage />} />
          <Route path="/ai-chat" element={<AIChatPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
        </Route>
        <Route element={<AuthGuard requireAdmin />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin/*" element={<AdminDashboard />} />
          </Route>
        </Route>
      </Routes>
      <BackToTop />
    </>
  )
}

export default App
