import { Suspense, lazy } from 'react'
import { Routes, Route } from 'react-router-dom'
import AuthGuard from './components/AuthGuard'
import AdminLayout from './components/AdminLayout'
import ScrollProgress from './components/ui/ScrollProgress'
import BackToTop from './components/ui/BackToTop'

const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const HomePage = lazy(() => import('./pages/HomePage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const BlogListPage = lazy(() => import('./pages/BlogListPage'))
const BlogDetailPage = lazy(() => import('./pages/BlogDetailPage'))
const ForumZoneListPage = lazy(() => import('./pages/ForumZoneListPage'))
const ForumPostListPage = lazy(() => import('./pages/ForumPostListPage'))
const ForumPostDetailPage = lazy(() => import('./pages/ForumPostDetailPage'))
const AIChatPage = lazy(() => import('./pages/AIChatPage'))
const PortfolioPage = lazy(() => import('./pages/PortfolioPage'))
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'))

function RouteFallback() {
  return null
}

function suspenseElement(element: React.ReactNode) {
  return <Suspense fallback={<RouteFallback />}>{element}</Suspense>
}

function App() {
  return (
    <>
      <ScrollProgress />
      <Routes>
        <Route path="/login" element={suspenseElement(<LoginPage />)} />
        <Route path="/register" element={suspenseElement(<RegisterPage />)} />
        <Route element={<AuthGuard />}>
          <Route path="/" element={suspenseElement(<HomePage />)} />
          <Route path="/profile" element={suspenseElement(<ProfilePage />)} />
          <Route path="/blogs" element={suspenseElement(<BlogListPage />)} />
          <Route path="/blogs/:slug" element={suspenseElement(<BlogDetailPage />)} />
          <Route path="/forums" element={suspenseElement(<ForumZoneListPage />)} />
          <Route path="/forums/z/:slug" element={suspenseElement(<ForumPostListPage />)} />
          <Route path="/forums/p/:postId" element={suspenseElement(<ForumPostDetailPage />)} />
          <Route path="/ai-chat" element={suspenseElement(<AIChatPage />)} />
          <Route path="/portfolio" element={suspenseElement(<PortfolioPage />)} />
        </Route>
        <Route element={<AuthGuard requireAdmin />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin/*" element={suspenseElement(<AdminDashboard />)} />
          </Route>
        </Route>
      </Routes>
      <BackToTop />
    </>
  )
}

export default App
