<script setup lang="ts">
import {
  Plus, Delete, Edit, Search, Refresh, View, Picture
} from '@element-plus/icons-vue'
import AppLayout from '@/components/Layout/AppLayout.vue'
import { sortFieldOptions, sortOrderOptions } from '@/types/album'
import { useAlbumManage } from './useAlbumManage'

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
  currentAlbum,
  formData,
  image1PreviewUrl,
  image2PreviewUrl,
  image1FileInputRef,
  image2FileInputRef,
  onImageFileSelected,
  clearImageSelection,
  openImagePicker,
  getAddedSongName,
  rules,
  formRef,
  handleSearch,
  handleReset,
  handlePageChange,
  handleSizeChange,
  handleSortChange,
  handleSelectionChange,
  handleAdd,
  handleEdit,
  handleSubmit,
  handleDelete,
  handleToggleStatus,
  handleBatchDelete,
  handleViewDetail,
  handleCloseDetail,
  handleEditCurrentAlbum,
  getRowClassName,
  formatDate
} = useAlbumManage()

function getImageSrc(row: typeof currentAlbum.value) {
  if (!row) return ''
  return row.image1Url || row.image2Url || ''
}
</script>

<template>
  <AppLayout title="专辑管理" :breadcrumb="['系统管理', '专辑管理']">
    <div class="album-manage">
      <!-- 搜索区域 -->
      <div class="search-section">
        <div class="search-form">
          <div class="form-item">
            <label>专辑名称</label>
            <el-input v-model="queryParams.albumName" placeholder="请输入专辑名称" clearable @keyup.enter="handleSearch" />
          </div>
          <div class="form-item">
            <label>作者</label>
            <el-input v-model="queryParams.authorName" placeholder="请输入作者昵称" clearable @keyup.enter="handleSearch" />
          </div>
          <div class="form-item">
            <label>推荐</label>
            <el-select v-model="queryParams.isRecommended" placeholder="全部" clearable>
              <el-option label="是" :value="true" />
              <el-option label="否" :value="false" />
            </el-select>
          </div>
          <div class="form-item">
            <label>是否下架</label>
            <el-select v-model="queryParams.isDeleted" placeholder="全部" clearable>
              <el-option label="已上架" :value="false" />
              <el-option label="已下架" :value="true" />
            </el-select>
          </div>
          <div class="form-item actions">
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </div>
        </div>
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
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增专辑</el-button>
          <el-button type="danger" :icon="Delete" :disabled="selectedRows.length === 0" @click="handleBatchDelete">
            批量删除
          </el-button>
        </div>
        <div class="right-info">共 <span class="highlight">{{ total }}</span> 条记录</div>
      </div>

      <!-- 表格区域 -->
      <div class="table-section">
        <el-table
          :data="tableData"
          v-loading="loading"
          stripe
          row-key="id"
          class="album-table"
          :row-class-name="getRowClassName"
          @selection-change="handleSelectionChange"
          @row-click="handleViewDetail"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="封面" width="100" align="center">
            <template #default="{ row }">
              <el-image
                v-if="getImageSrc(row)"
                :src="getImageSrc(row)"
                :preview-src-list="[getImageSrc(row)]"
                fit="cover"
                class="album-cover-thumb"
              />
              <div v-else class="album-cover-placeholder">
                <el-icon :size="28"><Picture /></el-icon>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="albumName" label="专辑名称" min-width="140" show-overflow-tooltip />
          <el-table-column label="作者" min-width="160" align="center">
            <template #default="{ row }">
              <div v-if="row.authorNames && row.authorNames.length" class="tag-list">
                <el-tag v-for="(name, idx) in row.authorNames.slice(0, 3)" :key="idx" size="small" class="item-tag">
                  {{ name }}
                </el-tag>
                <el-tag v-if="row.authorNames.length > 3" size="small" type="info">+{{ row.authorNames.length - 3 }}</el-tag>
              </div>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column label="歌曲" width="100" align="center">
            <template #default="{ row }">
              <el-tooltip v-if="row.songIds && row.songIds.length" :content="row.songIds.join('、')" placement="top">
                <el-tag size="small" type="info">{{ row.songIds.length }}首</el-tag>
              </el-tooltip>
              <span v-else class="text-muted">0首</span>
            </template>
          </el-table-column>
          <el-table-column label="标签" min-width="160" align="center">
            <template #default="{ row }">
              <div class="tag-list">
                <el-tag v-for="tag in (row.emoTags || []).slice(0, 2)" :key="tag" size="small" type="warning" class="item-tag">{{ tag }}</el-tag>
                <el-tag v-for="tag in (row.interestTags || []).slice(0, 2)" :key="tag" size="small" type="success" class="item-tag">{{ tag }}</el-tag>
                <span v-if="!(row.emoTags?.length || row.interestTags?.length)" class="text-muted">-</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="collectCount" label="收藏" width="80" align="center" />
          <el-table-column prop="playCount" label="播放" width="80" align="center" />
          <el-table-column prop="hot" label="热度" width="80" align="center" />
          <el-table-column label="推荐" width="85" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.isRecommended ? 'success' : 'info'" effect="dark">
                {{ row.isRecommended ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <span @click.stop @mousedown.stop>
                <el-switch
                  v-model="row.isDeleted"
                  :active-value="false"
                  :inactive-value="true"
                  active-text="上架"
                  inactive-text="下架"
                  inline-prompt
                  style="--el-switch-on-color: #10b981; --el-switch-off-color: #ef4444"
                  @change="(val: boolean) => handleToggleStatus(row, val)"
                />
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" min-width="160" align="center">
            <template #default="{ row }">{{ formatDate(row.createTime) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right" align="center">
            <template #default="{ row }">
              <el-button type="primary" link :icon="Edit" @click.stop="handleEdit(row)">编辑</el-button>
              <el-button type="danger" link :icon="Delete" @click.stop="handleDelete(row)">删除</el-button>
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
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <!-- 详情弹窗 -->
      <el-dialog v-model="detailDialogVisible" title="专辑详情" width="720px" class="album-dialog detail-dialog">
        <div v-if="currentAlbum" class="detail-body">
          <div class="detail-layout">
            <div class="detail-cover">
              <el-image v-if="currentAlbum.image1Url" :src="currentAlbum.image1Url" fit="cover" class="cover-large" />
              <div v-else class="cover-large-placeholder">
                <el-icon :size="48"><Picture /></el-icon>
              </div>
              <el-image v-if="currentAlbum.image2Url" :src="currentAlbum.image2Url" fit="cover" class="cover-secondary" />
            </div>
            <div class="detail-info">
              <div class="detail-section">
                <div class="section-title">基本信息</div>
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">专辑名称</span>
                    <span class="detail-value">{{ currentAlbum.albumName }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">来源</span>
                    <span class="detail-value">{{ currentAlbum.source || '-' }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">推荐</span>
                    <el-tag size="small" :type="currentAlbum.isRecommended ? 'success' : 'info'" effect="dark">
                      {{ currentAlbum.isRecommended ? '是' : '否' }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <div class="detail-section">
                <div class="section-title">数据统计</div>
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">热度</span>
                    <span class="detail-value highlight-hot">{{ currentAlbum.hot || 0 }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">播放数</span>
                    <span class="detail-value">{{ currentAlbum.playCount || 0 }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">收藏数</span>
                    <span class="detail-value">{{ currentAlbum.collectCount || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <div class="section-title">作者</div>
            <div v-if="currentAlbum.authorNames && currentAlbum.authorNames.length" class="tags-area">
              <el-tag v-for="name in currentAlbum.authorNames" :key="name" size="small" class="detail-tag">{{ name }}</el-tag>
            </div>
            <span v-else class="text-muted">暂无作者</span>
          </div>

          <div class="detail-section">
            <div class="section-title">歌曲（{{ currentAlbum.songIds?.length || 0 }}首）</div>
            <div v-if="currentAlbum.songIds && currentAlbum.songIds.length" class="tags-area">
              <el-tag v-for="sid in currentAlbum.songIds" :key="sid" size="small" class="detail-tag">歌曲{{ sid }}</el-tag>
            </div>
            <span v-else class="text-muted">暂无歌曲</span>
          </div>

          <div class="detail-section" v-if="currentAlbum.albumDescription">
            <div class="section-title">专辑描述</div>
            <div class="detail-desc">{{ currentAlbum.albumDescription }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">标签</div>
            <div class="tags-area">
              <el-tag v-for="tag in currentAlbum.emoTags || []" :key="tag" size="small" type="warning" class="detail-tag">{{ tag }}</el-tag>
              <el-tag v-for="tag in currentAlbum.interestTags || []" :key="tag" size="small" type="success" class="detail-tag">{{ tag }}</el-tag>
              <span v-if="!(currentAlbum.emoTags?.length || currentAlbum.interestTags?.length)" class="text-muted">暂无标签</span>
            </div>
          </div>

          <div class="detail-section">
            <div class="section-title">时间信息</div>
            <div class="detail-grid time-grid">
              <div class="detail-item">
                <span class="detail-label">创建时间</span>
                <span class="detail-value">{{ formatDate(currentAlbum.createTime) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">更新时间</span>
                <span class="detail-value">{{ formatDate(currentAlbum.updateTime) }}</span>
              </div>
            </div>
          </div>
        </div>
        <template #footer>
          <el-button @click="handleCloseDetail">关闭</el-button>
          <el-button v-if="currentAlbum" type="primary" @click="handleEditCurrentAlbum">编辑</el-button>
        </template>
      </el-dialog>

      <!-- 新增/编辑弹窗 -->
      <el-dialog v-model="dialogVisible" :title="dialogTitle" width="720px" class="album-dialog">
        <el-form ref="formRef" :model="formData" :rules="rules" label-width="96px" class="album-form">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="专辑名称" prop="albumName">
                <el-input v-model="formData.albumName" placeholder="请输入专辑名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="来源">
                <el-input v-model="formData.source" placeholder="专辑来源" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="专辑描述">
            <el-input v-model="formData.albumDescription" type="textarea" :rows="2" placeholder="请输入专辑描述" />
          </el-form-item>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="封面图1">
                <div class="image-edit-row">
                  <input ref="image1FileInputRef" type="file" accept="image/*" class="file-input" @change="onImageFileSelected(1, $event)" />
                  <el-image v-if="image1PreviewUrl || formData.image1Url" :src="image1PreviewUrl || formData.image1Url" fit="cover" class="image-preview" />
                  <div v-else class="image-preview-placeholder">
                    <el-icon :size="24"><Picture /></el-icon>
                  </div>
                  <div class="image-actions">
                    <el-button type="primary" plain size="small" @click="openImagePicker(1)">选择图片</el-button>
                    <el-button v-if="image1PreviewUrl" link type="danger" size="small" @click="clearImageSelection(1)">清除</el-button>
                  </div>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="封面图2">
                <div class="image-edit-row">
                  <input ref="image2FileInputRef" type="file" accept="image/*" class="file-input" @change="onImageFileSelected(2, $event)" />
                  <el-image v-if="image2PreviewUrl || formData.image2Url" :src="image2PreviewUrl || formData.image2Url" fit="cover" class="image-preview" />
                  <div v-else class="image-preview-placeholder">
                    <el-icon :size="24"><Picture /></el-icon>
                  </div>
                  <div class="image-actions">
                    <el-button type="primary" plain size="small" @click="openImagePicker(2)">选择图片</el-button>
                    <el-button v-if="image2PreviewUrl" link type="danger" size="small" @click="clearImageSelection(2)">清除</el-button>
                  </div>
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="推荐">
                <el-switch v-model="formData.isRecommended" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 情绪/兴趣标签（只读，由关联歌曲聚合） -->
          <el-form-item label="情绪标签">
            <div v-if="formData.emoTags && formData.emoTags.length" class="tags-readonly">
              <el-tag v-for="tag in formData.emoTags" :key="tag" size="small" type="warning" class="edit-tag">{{ tag }}</el-tag>
            </div>
            <span v-else class="text-muted">暂无（由歌曲汇总）</span>
          </el-form-item>
          <el-form-item label="兴趣标签">
            <div v-if="formData.interestTags && formData.interestTags.length" class="tags-readonly">
              <el-tag v-for="tag in formData.interestTags" :key="tag" size="small" type="success" class="edit-tag">{{ tag }}</el-tag>
            </div>
            <span v-else class="text-muted">暂无（由歌曲汇总）</span>
          </el-form-item>
        </el-form>

        <!-- 作者（只读，由后端根据关联歌曲聚合） -->
        <div class="relation-panel">
          <div class="panel-title">作者</div>
          <div v-if="formData.authorIds && formData.authorIds.length" class="relation-list">
            <el-tag
              v-for="(id, idx) in formData.authorIds"
              :key="id"
              size="small"
              class="relation-tag"
            >
              {{ formData.authorNames?.[idx] || `用户${id}` }} (ID: {{ id }})
            </el-tag>
          </div>
          <el-empty v-else description="暂无作者（请在音乐管理中为歌曲设置所属专辑）" :image-size="60" />
        </div>

        <!-- 歌曲（只读，在音乐管理中维护专辑归属） -->
        <div class="relation-panel">
          <div class="panel-title">歌曲</div>
          <div v-if="formData.songIds && formData.songIds.length" class="relation-list">
            <el-tag
              v-for="id in formData.songIds"
              :key="id"
              size="small"
              class="relation-tag"
            >
              {{ getAddedSongName(id) }} (ID: {{ id }})
            </el-tag>
          </div>
          <el-empty v-else description="暂无歌曲（请在音乐管理中将歌曲归入本专辑）" :image-size="60" />
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
<style scoped src="./album-manage.css"></style>
