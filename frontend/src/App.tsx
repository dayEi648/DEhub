import { Routes, Route, Outlet } from 'react-router-dom'
import MainLayout from '@/components/layout/MainLayout'
import AdminLayout from '@/components/layout/AdminLayout'

// Public pages
import LoginPage from '@/pages/public/LoginPage'
import RegisterPage from '@/pages/public/RegisterPage'

// Main pages
import DashboardPage from '@/pages/main/DashboardPage'
import BlogListPage from '@/pages/main/BlogListPage'
import BlogDetailPage from '@/pages/main/BlogDetailPage'
import ForumHomePage from '@/pages/main/ForumHomePage'
import ZonePostsPage from '@/pages/main/ZonePostsPage'
import PostDetailPage from '@/pages/main/PostDetailPage'
import AIChatPage from '@/pages/main/AIChatPage'
import ProfilePage from '@/pages/main/ProfilePage'
import FavoritesPage from '@/pages/main/FavoritesPage'
import FollowsPage from '@/pages/main/FollowsPage'
import SettingsPage from '@/pages/main/SettingsPage'

// Admin pages
import AdminDashboardPage from '@/pages/admin/AdminDashboardPage'
import AdminUsersPage from '@/pages/admin/AdminUsersPage'
import AdminBlogCategoriesPage from '@/pages/admin/AdminBlogCategoriesPage'
import AdminBlogPostsPage from '@/pages/admin/AdminBlogPostsPage'
import AdminForumZonesPage from '@/pages/admin/AdminForumZonesPage'
import AdminSystemLogsPage from '@/pages/admin/AdminSystemLogsPage'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Main routes */}
      <Route element={<MainLayout><Outlet /></MainLayout>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/" element={<DashboardPage />} />
        <Route path="/blog" element={<BlogListPage />} />
        <Route path="/blog/:slug" element={<BlogDetailPage />} />
        <Route path="/forum" element={<ForumHomePage />} />
        <Route path="/forum/:zoneSlug" element={<ZonePostsPage />} />
        <Route path="/forum/post/:postId" element={<PostDetailPage />} />
        <Route path="/ai-chat" element={<AIChatPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/favorites" element={<FavoritesPage />} />
        <Route path="/follows" element={<FollowsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Admin routes */}
      <Route element={<AdminLayout><Outlet /></AdminLayout>}>
        <Route path="/admin" element={<AdminDashboardPage />} />
        <Route path="/admin/users" element={<AdminUsersPage />} />
        <Route path="/admin/blog-categories" element={<AdminBlogCategoriesPage />} />
        <Route path="/admin/blog-posts" element={<AdminBlogPostsPage />} />
        <Route path="/admin/forum-zones" element={<AdminForumZonesPage />} />
        <Route path="/admin/system-logs" element={<AdminSystemLogsPage />} />
      </Route>
    </Routes>
  )
}

export default App
