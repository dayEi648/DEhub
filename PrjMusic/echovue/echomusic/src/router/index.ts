import { createRouter, createWebHistory } from 'vue-router'
import { pageLoadingState } from '@/components/PageLoading'
import { getToken, getUser } from '@/utils/authStorage'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/home' },
    {
      path: '/home',
      name: 'home',
      component: () => import('@/views/home/HomePage.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/Login.vue')
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/Register.vue')
    },
    {
      path: '/users',
      name: 'users',
      meta: { requiresAdmin: true },
      component: () => import('@/views/user/UserManage.vue')
    },
    {
      path: '/music',
      name: 'music',
      meta: { requiresAdmin: true },
      component: () => import('@/views/music/MusicManage.vue')
    },
    {
      path: '/albums',
      name: 'albums',
      meta: { requiresAdmin: true },
      component: () => import('@/views/album/AlbumManage.vue')
    },
    {
      path: '/banners',
      name: 'banners',
      meta: { requiresAdmin: true },
      component: () => import('@/views/banner/BannerManage.vue')
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/profile/ProfilePage.vue')
    },
    {
      path: '/profile/history',
      name: 'profile-history',
      component: () => import('@/views/profile/ProfileDetailPage.vue')
    },
    {
      path: '/profile/playlists',
      name: 'profile-playlists',
      component: () => import('@/views/profile/ProfileDetailPage.vue')
    },
    {
      path: '/profile/collected-playlists',
      name: 'profile-collected-playlists',
      component: () => import('@/views/profile/ProfileDetailPage.vue')
    },
    {
      path: '/profile/collected-albums',
      name: 'profile-collected-albums',
      component: () => import('@/views/profile/ProfileDetailPage.vue')
    },
    {
      path: '/discover',
      name: 'discover',
      component: () => import('@/views/discover/DiscoverPage.vue')
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/search/SearchResultPage.vue')
    },
    {
      path: '/music/:id',
      name: 'player',
      component: () => import('@/views/player/PlayerPage.vue')
    },
    {
      path: '/playlist/:id',
      name: 'playlist-detail',
      component: () => import('@/views/detail/PlaylistDetailPage.vue')
    },
    {
      path: '/album/:id',
      name: 'album-detail',
      component: () => import('@/views/detail/PlaylistDetailPage.vue')
    },
    {
      path: '/user/:id',
      name: 'user-detail',
      component: () => import('@/views/user-detail/UserDetailPage.vue')
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/views/notification/NotificationPage.vue')
    },
    {
      path: '/private-messages/:conversationKey',
      name: 'private-message-detail',
      component: () => import('@/views/notification/PrivateMessagePage.vue')
    },
    {
      path: '/ai-chat',
      name: 'ai-chat',
      component: () => import('@/views/ai/AiChatPage.vue')
    },
    { path: '/:pathMatch(.*)*', redirect: '/home' }
  ]
})

// 路由前置守卫：鉴权 + 加载动画
router.beforeEach((to, from, next) => {
  // 避免同一路由重复触发
  const isSameRoutePattern = to.name === from.name
  const isProfileSwitch = to.path.startsWith('/profile/') && from.path.startsWith('/profile/')
  if (to.path !== from.path && !isSameRoutePattern && !isProfileSwitch) {
    pageLoadingState.show()
  }

  const isAuthenticated = !!getToken()
  const isAuthPage = to.path === '/login' || to.path === '/register'

  if (!isAuthenticated && !isAuthPage) {
    next('/login')
  } else if (isAuthenticated && isAuthPage) {
    next('/home')
  } else if (to.meta.requiresAdmin) {
    const user = getUser()
    const isAdmin = (user?.role ?? 0) >= 2
    if (!isAdmin) {
      next('/home')
    } else {
      next()
    }
  } else {
    next()
  }
})

// 路由后置守卫：隐藏加载动画
router.afterEach(() => {
  pageLoadingState.hide()
})

// 错误处理
router.onError(() => {
  pageLoadingState.hideImmediately()
})

export default router
