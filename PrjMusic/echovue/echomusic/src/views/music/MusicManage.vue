<script setup lang="ts">
import { Delete, Edit, Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import AppLayout from '@/components/Layout/AppLayout.vue'
import { sortFieldOptions, sortOrderOptions, roleOptions } from '@/types/music'
import { useMusicManage } from './useMusicManage'

const {
  queryParams,
  tableData,
  total,
  loading,
  selectedRows,
  dialogVisible,
  detailDialogVisible,
  dialogTitle,
  isEdit,
  currentMusic,
  formData,
  pendingMusicFiles,
  refMusicAudio,
  refMusicLyrics,
  refMusicImg1,
  refMusicImg2,
  refMusicImg3,
  onPendingMusicFileChange,
  openMusicFilePicker,
  newAuthorId,
  userCache,
  authorNames,
  selectedAuthor,
  authorSearchLoading,
  authorSearchOptions,
  emoTagInputVisible,
  emoTagInputValue,
  emoTagInputRef,
  interestTagInputVisible,
  interestTagInputValue,
  interestTagInputRef,
  langInputVisible,
  langInputValue,
  langInputRef,
  instrumentInputVisible,
  instrumentInputValue,
  instrumentInputRef,
  rules,
  formRef,
  handleAdd,
  handleEdit,
  handleViewDetail,
  handleCloseDetail,
  handleEditCurrentMusic,
  handleDelete,
  handleBatchDelete,
  handleSubmit,
  handleSearch,
  handleReset,
  handleSortChange,
  handleSelectionChange,
  handlePageChange,
  handleSizeChange,
  handleToggleRecommend,
  handleToggleStatus,
  formatDate,
  getAuthorNames,
  addAuthorId,
  removeAuthorId,
  searchAuthors,
  addAuthor,
  albumSearchKeyword,
  albumSearchLoading,
  albumSearchOptions,
  selectedAlbum,
  searchAlbumList,
  selectAlbum,
  clearAlbumSelection,
  queryAlbumSearchLoading,
  queryAlbumSearchOptions,
  selectedQueryAlbum,
  searchAlbumListForQuery,
  onQueryAlbumChange,
  showEmoTagInput,
  handleEmoTagConfirm,
  handleEmoTagClose,
  showInterestTagInput,
  handleInterestTagConfirm,
  handleInterestTagClose,
  showLangInput,
  handleLangConfirm,
  handleLangClose,
  showInstrumentInput,
  handleInstrumentConfirm,
  handleInstrumentClose
} = useMusicManage()
</script>

<template>
  <AppLayout title="音乐管理" :breadcrumb="['系统管理', '音乐管理']">
    <div class="music-manage">
      <!-- 搜索区域 -->
      <div class="search-section">
        <div class="search-form">
          <div class="form-item">
            <label>音乐名称</label>
            <el-input v-model="queryParams.musicName" clearable placeholder="请输入音乐名称" @keyup.enter="handleSearch" />
          </div>
          <div class="form-item">
            <label>风格</label>
            <el-input v-model="queryParams.style" clearable placeholder="请输入风格" @keyup.enter="handleSearch" />
          </div>
          <div class="form-item">
            <label>VIP</label>
            <el-select v-model="queryParams.vip" clearable placeholder="全部">
              <el-option label="普通" :value="false" />
              <el-option label="VIP" :value="true" />
            </el-select>
          </div>
          <div class="form-item">
            <label>所属专辑</label>
            <el-select
              v-model="selectedQueryAlbum"
              value-key="id"
              filterable
              remote
              reserve-keyword
              placeholder="输入专辑名称搜索"
              :remote-method="searchAlbumListForQuery"
              :loading="queryAlbumSearchLoading"
              clearable
              style="width: 100%"
              @change="onQueryAlbumChange"
            >
              <el-option
                v-for="album in queryAlbumSearchOptions"
                :key="album.id"
                :label="`${album.albumName} (ID: ${album.id})`"
                :value="album"
              />
            </el-select>
          </div>
          <div class="form-item">
            <label>推荐</label>
            <el-select v-model="queryParams.isRecommended" clearable placeholder="全部">
              <el-option label="是" :value="true" />
              <el-option label="否" :value="false" />
            </el-select>
          </div>
          <div class="form-item">
            <label>状态</label>
            <el-select v-model="queryParams.isDeleted" clearable placeholder="全部">
              <el-option label="正常" :value="false" />
              <el-option label="已删除" :value="true" />
            </el-select>
          </div>
          <div class="form-item actions">
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </div>
        </div>
        <!-- 排序区域 -->
        <div class="sort-section">
          <span class="sort-label">排序:</span>
          <el-select v-model="queryParams.sortBy" size="small" @change="handleSortChange">
            <el-option v-for="item in sortFieldOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="queryParams.sortOrder" size="small" @change="handleSortChange">
            <el-option v-for="item in sortOrderOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
      </div>

      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="left-actions">
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增音乐</el-button>
          <el-button type="danger" :icon="Delete" :disabled="selectedRows.length === 0" @click="handleBatchDelete">
            批量删除
          </el-button>
        </div>
        <div class="right-info">共 <span class="highlight">{{ total }}</span> 条记录</div>
      </div>

      <!-- 表格区域 -->
      <div class="table-section">
        <el-table :data="tableData" v-loading="loading" stripe row-key="id" class="music-table" @selection-change="handleSelectionChange">
          <el-table-column type="selection" min-width="25" align="center" />
          <el-table-column prop="musicName" label="音乐名称" min-width="100" show-overflow-tooltip />
                    <el-table-column label="作者" min-width="150" align="center">
            <template #default="{ row }">
              <span v-if="row.authorIds && row.authorIds.length" class="author-names">
                {{ getAuthorNames(row.authorIds) }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="albumName" label="专辑名" min-width="120" align="center" show-overflow-tooltip />
          <el-table-column label="VIP" min-width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.vip ? 'warning' : 'info'" effect="dark">
                {{ row.vip ? 'VIP' : '普通' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="style" label="风格" min-width="100" align="center" />
          <el-table-column prop="releaseDate" label="发行日期" min-width="100" align="center" />
          <el-table-column prop="hot" label="热度" min-width="80" align="center" />
          <el-table-column label="推荐" min-width="80" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.isRecommended"
                inline-prompt
                active-text="是"
                inactive-text="否"
                @change="handleToggleRecommend(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="状态" min-width="80" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.normalStatus"
                :active-value="true"
                :inactive-value="false"
                inline-prompt
                active-text="正常"
                inactive-text="已删"
                @change="handleToggleStatus(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="100" fixed="right" align="center">
            <template #default="{ row }">
              <el-button type="primary" link :icon="View" @click="handleViewDetail(row)">查看</el-button>
              <el-button type="primary" link :icon="Edit" @click="handleEdit(row)">编辑</el-button>
              <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="queryParams.pageNum"
            v-model:page-size="queryParams.pageSize"
            :page-sizes="[10, 20, 50]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </div>

      <!-- 详情弹窗 -->
      <el-dialog v-model="detailDialogVisible" title="音乐详情" width="720px" class="music-dialog detail-dialog">
        <div v-if="currentMusic" class="detail-body">
          <!-- 基本信息区域 -->
          <div class="detail-section">
            <div class="section-title">基本信息</div>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">音乐名称</span>
                <span class="detail-value">{{ currentMusic.musicName }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">专辑名</span>
                <span class="detail-value">{{ currentMusic.albumName || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">风格</span>
                <span class="detail-value">{{ currentMusic.style || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">发行日期</span>
                <span class="detail-value">{{ currentMusic.releaseDate || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">VIP</span>
                <el-tag size="small" :type="currentMusic.vip ? 'warning' : 'info'" effect="dark">
                  {{ currentMusic.vip ? 'VIP' : '普通' }}
                </el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">推荐</span>
                <el-tag size="small" :type="currentMusic.isRecommended ? 'success' : 'info'" effect="dark">
                  {{ currentMusic.isRecommended ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">状态</span>
                <el-tag size="small" :type="currentMusic.isDeleted ? 'danger' : 'success'" effect="dark">
                  {{ currentMusic.isDeleted ? '已删除' : '正常' }}
                </el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">来源</span>
                <span class="detail-value">{{ currentMusic.source || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 数据统计区域 -->
          <div class="detail-section">
            <div class="section-title">数据统计</div>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">热度</span>
                <span class="detail-value highlight-hot">{{ currentMusic.hot || 0 }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">播放量</span>
                <span class="detail-value">{{ currentMusic.playCount || 0 }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">评论数</span>
                <span class="detail-value">{{ currentMusic.commentCount || 0 }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">收藏数</span>
                <span class="detail-value">{{ currentMusic.collectCount || 0 }}</span>
              </div>
            </div>
          </div>

          <!-- 作者区域 -->
          <div class="detail-section" v-if="currentMusic.authorIds && currentMusic.authorIds.length > 0">
            <div class="section-title">作者</div>
            <div class="tags-area">
              <el-tag v-for="id in currentMusic.authorIds" :key="id" size="small" class="detail-tag">
                {{ authorNames.get(String(id)) || `用户${id}` }}
              </el-tag>
            </div>
          </div>

          <!-- 情绪标签区域 -->
          <div class="detail-section" v-if="currentMusic.emoTags && currentMusic.emoTags.length > 0">
            <div class="section-title">情绪标签</div>
            <div class="tags-area">
              <el-tag v-for="tag in currentMusic.emoTags" :key="tag" size="small" class="detail-tag">{{ tag }}</el-tag>
            </div>
          </div>

          <!-- 兴趣标签区域 -->
          <div class="detail-section" v-if="currentMusic.interestTags && currentMusic.interestTags.length > 0">
            <div class="section-title">兴趣标签</div>
            <div class="tags-area">
              <el-tag v-for="tag in currentMusic.interestTags" :key="tag" size="small" class="detail-tag">{{ tag }}</el-tag>
            </div>
          </div>

          <!-- 语言区域 -->
          <div class="detail-section" v-if="currentMusic.languages && currentMusic.languages.length > 0">
            <div class="section-title">语言</div>
            <div class="tags-area">
              <el-tag v-for="lang in currentMusic.languages" :key="lang" size="small" class="detail-tag">{{ lang }}</el-tag>
            </div>
          </div>

          <!-- 乐器区域 -->
          <div class="detail-section" v-if="currentMusic.instruments && currentMusic.instruments.length > 0">
            <div class="section-title">乐器</div>
            <div class="tags-area">
              <el-tag v-for="inst in currentMusic.instruments" :key="inst" size="small" class="detail-tag">{{ inst }}</el-tag>
            </div>
          </div>

          <!-- 文件信息区域 -->
          <div class="detail-section">
            <div class="section-title">文件信息</div>
            <div class="detail-list">
              <div class="detail-list-item">
                <span class="detail-label">音频URL</span>
                <span class="detail-value url-value">{{ currentMusic.fileUrl || '-' }}</span>
              </div>
              <div class="detail-list-item">
                <span class="detail-label">歌词URL</span>
                <span class="detail-value url-value">{{ currentMusic.lyricsUrl || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 时间信息区域 -->
          <div class="detail-section">
            <div class="section-title">时间信息</div>
            <div class="detail-grid time-grid">
              <div class="detail-item">
                <span class="detail-label">创建时间</span>
                <span class="detail-value">{{ formatDate(currentMusic.createTime) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">更新时间</span>
                <span class="detail-value">{{ formatDate(currentMusic.updateTime) }}</span>
              </div>
            </div>
          </div>
        </div>
        <template #footer>
          <el-button @click="handleCloseDetail">关闭</el-button>
          <el-button v-if="currentMusic" type="primary" @click="handleEditCurrentMusic">编辑</el-button>
        </template>
      </el-dialog>

      <!-- 新增/编辑弹窗 -->
      <el-dialog v-model="dialogVisible" :title="dialogTitle" width="760px" class="music-dialog">
        <el-form ref="formRef" :model="formData" :rules="rules" label-width="96px" class="music-form">
          <!-- 第一行：音乐名称 + 专辑ID -->
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="音乐名称" prop="musicName">
                <el-input v-model="formData.musicName" placeholder="请输入音乐名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="所属专辑">
                <el-select
                  v-model="selectedAlbum"
                  value-key="id"
                  filterable
                  remote
                  reserve-keyword
                  placeholder="输入专辑名称搜索"
                  :remote-method="searchAlbumList"
                  :loading="albumSearchLoading"
                  style="width: 100%"
                  clearable
                  @change="selectAlbum"
                  @clear="clearAlbumSelection"
                >
                  <el-option
                    v-for="album in albumSearchOptions"
                    :key="album.id"
                    :label="`${album.albumName} (ID: ${album.id})`"
                    :value="album"
                  />
                </el-select>
                <div v-if="(formData.albumId && formData.albumId !== -1) || selectedAlbum" class="album-selected">
                  <el-tag size="small" closable @close="clearAlbumSelection">
                    {{ selectedAlbum?.albumName || `专辑ID: ${formData.albumId}` }}
                  </el-tag>
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第二行：风格 + 热度 -->
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="风格">
                <el-input v-model="formData.style" placeholder="如：流行、摇滚" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="热度">
                <el-input-number v-model="formData.hot" :min="0" :max="1000" placeholder="0-1000" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第三行：VIP + 推荐 -->
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="VIP">
                <el-switch v-model="formData.vip" :active-value="true" :inactive-value="false" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="推荐">
                <el-switch v-model="formData.isRecommended" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第四行：来源 -->
          <el-form-item label="来源">
            <el-input v-model="formData.source" placeholder="音乐来源" />
          </el-form-item>

          <!-- 第五行：音频 + 歌词文件（确定时上传 OSS） -->
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="音频文件">
                <div class="file-pick-row">
                  <input
                    ref="refMusicAudio"
                    type="file"
                    accept=".mp3,.flac,.wav,.m4a,.aac,.ogg,audio/*"
                    class="music-file-input"
                    @change="onPendingMusicFileChange('file', $event)"
                  />
                  <el-button type="primary" plain @click="openMusicFilePicker('audio')">选择文件</el-button>
                  <span class="file-pick-name">{{ pendingMusicFiles.file?.name || '未选择新文件' }}</span>
                  <el-button v-if="pendingMusicFiles.file" link type="danger" @click="pendingMusicFiles.file = null">清除</el-button>
                </div>
                <div v-if="isEdit && formData.fileUrl" class="file-hint">当前：{{ formData.fileUrl }}</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="歌词文件">
                <div class="file-pick-row">
                  <input
                    ref="refMusicLyrics"
                    type="file"
                    accept=".lrc,.txt"
                    class="music-file-input"
                    @change="onPendingMusicFileChange('lyricsFile', $event)"
                  />
                  <el-button type="primary" plain @click="openMusicFilePicker('lyrics')">选择文件</el-button>
                  <span class="file-pick-name">{{ pendingMusicFiles.lyricsFile?.name || '未选择新文件' }}</span>
                  <el-button v-if="pendingMusicFiles.lyricsFile" link type="danger" @click="pendingMusicFiles.lyricsFile = null">清除</el-button>
                </div>
                <div v-if="isEdit && formData.lyricsUrl" class="file-hint">当前：{{ formData.lyricsUrl }}</div>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第六行：封面图片 -->
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="封面1">
                <div class="file-pick-row file-pick-row--stack">
                  <input
                    ref="refMusicImg1"
                    type="file"
                    accept="image/*"
                    class="music-file-input"
                    @change="onPendingMusicFileChange('image1File', $event)"
                  />
                  <el-button type="primary" plain size="small" @click="openMusicFilePicker('img1')">选择图片</el-button>
                  <span class="file-pick-name">{{ pendingMusicFiles.image1File?.name || '未选' }}</span>
                  <el-button v-if="pendingMusicFiles.image1File" link type="danger" size="small" @click="pendingMusicFiles.image1File = null">清除</el-button>
                  <div v-if="isEdit && formData.image1Url" class="file-hint">当前图：已上传</div>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="封面2">
                <div class="file-pick-row file-pick-row--stack">
                  <input
                    ref="refMusicImg2"
                    type="file"
                    accept="image/*"
                    class="music-file-input"
                    @change="onPendingMusicFileChange('image2File', $event)"
                  />
                  <el-button type="primary" plain size="small" @click="openMusicFilePicker('img2')">选择图片</el-button>
                  <span class="file-pick-name">{{ pendingMusicFiles.image2File?.name || '未选' }}</span>
                  <el-button v-if="pendingMusicFiles.image2File" link type="danger" size="small" @click="pendingMusicFiles.image2File = null">清除</el-button>
                  <div v-if="isEdit && formData.image2Url" class="file-hint">当前图：已上传</div>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="封面3">
                <div class="file-pick-row file-pick-row--stack">
                  <input
                    ref="refMusicImg3"
                    type="file"
                    accept="image/*"
                    class="music-file-input"
                    @change="onPendingMusicFileChange('image3File', $event)"
                  />
                  <el-button type="primary" plain size="small" @click="openMusicFilePicker('img3')">选择图片</el-button>
                  <span class="file-pick-name">{{ pendingMusicFiles.image3File?.name || '未选' }}</span>
                  <el-button v-if="pendingMusicFiles.image3File" link type="danger" size="small" @click="pendingMusicFiles.image3File = null">清除</el-button>
                  <div v-if="isEdit && formData.image3Url" class="file-hint">当前图：已上传</div>
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第七行：发行日期 -->
          <el-form-item label="发行日期">
            <el-date-picker v-model="formData.releaseDate" value-format="YYYY-MM-DD" type="date" placeholder="选择日期" style="width: 100%" />
          </el-form-item>

          <!-- 第八行：情绪标签 -->
          <el-form-item label="情绪标签">
            <div class="tags-edit">
              <el-tag v-for="tag in formData.emoTags" :key="tag" closable class="edit-tag" @close="handleEmoTagClose(tag)">
                {{ tag }}
              </el-tag>
              <el-input v-if="emoTagInputVisible" ref="emoTagInputRef" v-model="emoTagInputValue" size="small" class="tag-input" @keyup.enter="handleEmoTagConfirm" @blur="handleEmoTagConfirm" />
              <el-button v-else size="small" class="tag-add-btn" @click="showEmoTagInput">+ 添加标签</el-button>
            </div>
          </el-form-item>

          <!-- 第九行：兴趣标签 -->
          <el-form-item label="兴趣标签">
            <div class="tags-edit">
              <el-tag v-for="tag in formData.interestTags" :key="tag" closable class="edit-tag" @close="handleInterestTagClose(tag)">
                {{ tag }}
              </el-tag>
              <el-input v-if="interestTagInputVisible" ref="interestTagInputRef" v-model="interestTagInputValue" size="small" class="tag-input" @keyup.enter="handleInterestTagConfirm" @blur="handleInterestTagConfirm" />
              <el-button v-else size="small" class="tag-add-btn" @click="showInterestTagInput">+ 添加标签</el-button>
            </div>
          </el-form-item>

          <!-- 第九行：语言 -->
          <el-form-item label="语言">
            <div class="tags-edit">
              <el-tag v-for="tag in formData.languages" :key="tag" closable class="edit-tag" @close="handleLangClose(tag)">
                {{ tag }}
              </el-tag>
              <el-input v-if="langInputVisible" ref="langInputRef" v-model="langInputValue" size="small" class="tag-input" @keyup.enter="handleLangConfirm" @blur="handleLangConfirm" />
              <el-button v-else size="small" class="tag-add-btn" @click="showLangInput">+ 添加语言</el-button>
            </div>
          </el-form-item>

          <!-- 第十行：乐器 -->
          <el-form-item label="乐器">
            <div class="tags-edit">
              <el-tag v-for="tag in formData.instruments" :key="tag" closable class="edit-tag" @close="handleInstrumentClose(tag)">
                {{ tag }}
              </el-tag>
              <el-input v-if="instrumentInputVisible" ref="instrumentInputRef" v-model="instrumentInputValue" size="small" class="tag-input" @keyup.enter="handleInstrumentConfirm" @blur="handleInstrumentConfirm" />
              <el-button v-else size="small" class="tag-add-btn" @click="showInstrumentInput">+ 添加乐器</el-button>
            </div>
          </el-form-item>
        </el-form>

        <!-- 作者关联面板 -->
        <div class="relation-panel">
          <div class="panel-title">作者关联</div>
          <div class="relation-form">
            <el-select
              v-model="selectedAuthor"
              filterable
              remote
              reserve-keyword
              placeholder="输入昵称搜索作者"
              :remote-method="searchAuthors"
              :loading="authorSearchLoading"
              style="width: 240px"
              clearable
              value-key="id"
            >
              <el-option
                v-for="user in authorSearchOptions"
                :key="user.id"
                :label="`${user.name || user.username} (ID: ${user.id})`"
                :value="user"
              />
            </el-select>
            <el-button type="primary" @click="addAuthor(selectedAuthor)">添加作者</el-button>
          </div>
          <div v-if="formData.authorIds && formData.authorIds.length" class="author-list">
            <el-tag
              v-for="id in formData.authorIds"
              :key="id"
              size="small"
              closable
              class="author-tag"
              @close="removeAuthorId(id)"
            >
              {{ userCache.get(Number(id)) || authorNames.get(id) || `用户${id}` }} (ID: {{ id }})
            </el-tag>
          </div>
          <el-empty v-else description="暂无作者" :image-size="60" />
        </div>

        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </template>
      </el-dialog>
    </div>
  </AppLayout>
</template>

<style scoped src="../../styles/common.css"></style>
<style scoped src="./music-manage.css"></style>
