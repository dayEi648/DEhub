import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { layout: 'blank', title: '登录' }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '首页' }
    },
    {
      path: '/blog',
      name: 'blog-list',
      component: () => import('@/views/blog/BlogListView.vue'),
      meta: { title: '博客' }
    },
    {
      path: '/blog/:slug',
      name: 'blog-detail',
      component: () => import('@/views/blog/BlogDetailView.vue'),
      meta: { title: '文章详情' }
    },
    {
      path: '/blog/new',
      name: 'blog-new',
      component: () => import('@/views/blog/BlogEditView.vue'),
      meta: { title: '撰写文章', requiresSuperAdmin: true }
    },
    {
      path: '/blog/edit/:slug',
      name: 'blog-edit',
      component: () => import('@/views/blog/BlogEditView.vue'),
      meta: { title: '编辑文章', requiresSuperAdmin: true }
    },
    {
      path: '/blog/admin',
      name: 'blog-admin',
      component: () => import('@/views/blog/BlogAdminView.vue'),
      meta: { title: '博客管理', requiresSuperAdmin: true }
    },
    {
      path: '/forum',
      name: 'forum-zones',
      component: () => import('@/views/forum/ForumZoneListView.vue'),
      meta: { title: '论坛' }
    },
    {
      path: '/forum/:zoneSlug',
      name: 'forum-posts',
      component: () => import('@/views/forum/ForumPostListView.vue'),
      meta: { title: '帖子列表' }
    },
    {
      path: '/forum/post/:postId',
      name: 'forum-post-detail',
      component: () => import('@/views/forum/ForumPostDetailView.vue'),
      meta: { title: '帖子详情' }
    },
    {
      path: '/forum/post/new',
      name: 'forum-post-new',
      component: () => import('@/views/forum/ForumPostEditView.vue'),
      meta: { title: '发表帖子' }
    },
    {
      path: '/forum/post/edit/:postId',
      name: 'forum-post-edit',
      component: () => import('@/views/forum/ForumPostEditView.vue'),
      meta: { title: '编辑帖子' }
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/chat/ChatView.vue'),
      meta: { title: 'AI 对话' }
    },
    {
      path: '/links',
      name: 'links',
      component: () => import('@/views/links/LinksView.vue'),
      meta: { title: '子网站' }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/user/ProfileView.vue'),
      meta: { title: '个人中心' }
    },
    {
      path: '/admin/users',
      name: 'user-admin',
      component: () => import('@/views/user/UserAdminView.vue'),
      meta: { title: '用户管理', requiresAdmin: true }
    },
    {
      path: '/404',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { layout: 'blank', title: '404' }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/404'
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  // Update document title
  if (to.meta.title) {
    document.title = `${to.meta.title} | DE hub`
  }

  // Auth check
  const isAuthenticated = authStore.isAuthenticated

  if (to.path === '/login') {
    if (isAuthenticated) {
      next('/')
    } else {
      next()
    }
    return
  }

  if (!isAuthenticated) {
    next('/login')
    return
  }

  // Permission check
  if (to.meta.requiresSuperAdmin && !authStore.isSuperAdmin) {
    next('/')
    return
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')
    return
  }

  next()
})

export default router
