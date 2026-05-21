import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './components/ui/Toast';
import CustomCursor from './components/effects/CustomCursor';
import Scanlines from './components/effects/Scanlines';
import TVBootAnimation from './components/effects/TVBootAnimation';
import AuthGuard from './components/auth/AuthGuard';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminForumZonesPage from './pages/admin/AdminForumZonesPage';
import AdminLogsPage from './pages/admin/AdminLogsPage';
import BlogListPage from './pages/BlogListPage';
import BlogDetailPage from './pages/BlogDetailPage';
import BlogEditPage from './pages/BlogEditPage';
import ForumZoneListPage from './pages/ForumZoneListPage';
import ForumZonePage from './pages/ForumZonePage';
import ForumPostDetailPage from './pages/ForumPostDetailPage';
import ForumPostEditPage from './pages/ForumPostEditPage';

function GlobalEffects() {
  const [bootDone, setBootDone] = useState(false);
  return (
    <>
      <CustomCursor />
      <Scanlines />
      {!bootDone && <TVBootAnimation onComplete={() => setBootDone(true)} />}
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <GlobalEffects />
          <Routes>
            <Route
              path="/login"
              element={
                <AuthGuard>
                  <LoginPage />
                </AuthGuard>
              }
            />
            <Route
              path="/register"
              element={
                <AuthGuard>
                  <RegisterPage />
                </AuthGuard>
              }
            />
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
              path="/admin"
              element={
                <AuthGuard requireAdmin>
                  <Navigate to="/admin/users" replace />
                </AuthGuard>
              }
            />
            <Route
              path="/admin/users"
              element={
                <AuthGuard requireAdmin>
                  <AdminUsersPage />
                </AuthGuard>
              }
            />
            <Route
              path="/admin/forum-zones"
              element={
                <AuthGuard requireAdmin>
                  <AdminForumZonesPage />
                </AuthGuard>
              }
            />
            <Route
              path="/admin/logs"
              element={
                <AuthGuard requireAdmin>
                  <AdminLogsPage />
                </AuthGuard>
              }
            />
            <Route
              path="/blog"
              element={
                <AuthGuard>
                  <BlogListPage />
                </AuthGuard>
              }
            />
            <Route
              path="/blog/:slug"
              element={
                <AuthGuard>
                  <BlogDetailPage />
                </AuthGuard>
              }
            />
            <Route
              path="/blog/create"
              element={
                <AuthGuard requireAdmin>
                  <BlogEditPage />
                </AuthGuard>
              }
            />
            <Route
              path="/blog/edit/:id"
              element={
                <AuthGuard requireAdmin>
                  <BlogEditPage />
                </AuthGuard>
              }
            />
            <Route
              path="/forum"
              element={
                <AuthGuard>
                  <ForumZoneListPage />
                </AuthGuard>
              }
            />
            <Route
              path="/forum/zones/:slug"
              element={
                <AuthGuard>
                  <ForumZonePage />
                </AuthGuard>
              }
            />
            <Route
              path="/forum/posts/:id"
              element={
                <AuthGuard>
                  <ForumPostDetailPage />
                </AuthGuard>
              }
            />
            <Route
              path="/forum/create"
              element={
                <AuthGuard>
                  <ForumPostEditPage />
                </AuthGuard>
              }
            />
            <Route
              path="/forum/edit/:id"
              element={
                <AuthGuard>
                  <ForumPostEditPage />
                </AuthGuard>
              }
            />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
