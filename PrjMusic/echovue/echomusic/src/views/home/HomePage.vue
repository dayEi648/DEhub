<script setup lang="ts">
import { CaretRight } from '@element-plus/icons-vue'
import HomeLayout from '@/components/HomeLayout/HomeLayout.vue'
import HeroSection from './sections/HeroSection.vue'
import PlaylistSection from './sections/PlaylistSection.vue'
import HotSongsSection from './sections/HotSongsSection.vue'
import NewSongsSection from './sections/NewSongsSection.vue'
import DailyQuoteSection from './sections/DailyQuoteSection.vue'
import { useHomePage } from './useHomePage'

const {
  searchKeyword,
  carouselList,
  playlistList,
  hotSongs,
  newSongs,
  displayName,
  handleSearch,
  goToAdmin,
  goToProfile,
  handleLogout,
  handleBannerClick,
  handlePlaySong,
  handlePlaylistClick
} = useHomePage()
</script>

<template>
  <HomeLayout
    v-model:search-keyword="searchKeyword"
    @search="handleSearch"
    @go-admin="goToAdmin"
    @go-profile="goToProfile"
    @logout="handleLogout"
  >
    <div class="home-page">
      <!-- Hero 欢迎区 -->
      <HeroSection :display-name="displayName" />

      <!-- 轮播图 -->
      <section class="hero-carousel-section">
        <el-carousel
          class="hero-carousel-v2"
          height="420px"
          arrow="never"
          indicator-position="outside"
          :interval="5000"
        >
          <el-carousel-item v-for="item in carouselList" :key="item.id">
            <div
              class="carousel-slide-v2"
              :style="{ backgroundImage: item.coverUrl ? `url(${item.coverUrl})` : 'none', backgroundSize: 'cover', backgroundPosition: 'center' }"
              @click="handleBannerClick(item)"
            >
              <div class="carousel-overlay-v2" />
              <div class="carousel-content-v2">
                <h2 class="carousel-title-v2">{{ item.title }}</h2>
                <p class="carousel-subtitle-v2">{{ item.description }}</p>
              </div>
            </div>
          </el-carousel-item>
        </el-carousel>
        <el-empty v-if="carouselList.length === 0" description="暂无推荐内容" :image-size="80" style="margin-top: 20px;" />
      </section>

      <!-- 推荐歌单 -->
      <PlaylistSection
        :playlists="playlistList"
        @click="handlePlaylistClick"
      />

      <!-- 热门音乐 -->
      <HotSongsSection
        :songs="hotSongs"
        @play="handlePlaySong"
      />

      <!-- 新歌速递 -->
      <NewSongsSection
        :songs="newSongs"
        @play="handlePlaySong"
      />

      <!-- 每日音乐金句 -->
      <DailyQuoteSection />

    </div>
  </HomeLayout>
</template>

<style scoped src="./home.css"></style>
