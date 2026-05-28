<script setup lang="ts">
import { Plus, Delete, Edit, Search, Refresh, UserFilled, CircleClose } from '@element-plus/icons-vue'
import AppLayout from '@/components/Layout/AppLayout.vue'
import { sortFieldOptions, sortOrderOptions, statusOptions, roleOptions, genderOptions } from '@/types/user'
import type { UserVO } from '@/types/user'
import { useUserManage } from './useUserManage'

const {
  queryParams,
  tableData,
  total,
  loading,
  selectedRows,
  dialogVisible,
  dialogTitle,
  isEdit,
  detailDialogVisible,
  currentUser,
  formData,
  avatarDisplaySrc,
  hasPendingAvatarFile,
  onAvatarFileSelected,
  clearAvatarSelection,
  avatarFileInputRef,
  openAvatarPicker,
  emoTagInputVisible,
  emoTagInputValue,
  emoTagInputRef,
  interestTagInputVisible,
  interestTagInputValue,
  interestTagInputRef,
  rules,
  formRef,
  showEmoTagInput,
  handleEmoTagConfirm,
  handleEmoTagClose,
  showInterestTagInput,
  handleInterestTagConfirm,
  handleInterestTagClose,
  handleSearch,
  handleReset,
  handlePageChange,
  handleSizeChange,
  handleSortChange,
  handleSelectionChange,
  handleAdd,
  handleEdit,
  handleSubmit,
  handleCancel,
  handleDelete,
  handleBatchDelete,
  getStatusType,
  getStatusLabel,
  getGenderLabel,
  getRoleLabel,
  getRowClassName,
  formatDate,
  handleViewDetail,
  handleCloseDetail,
  handleEditCurrentUser,
  canManage,
  availableRoleOptions
} = useUserManage()
</script>

<template>
  <AppLayout title="用户管理" :breadcrumb="['系统管理', '用户管理']">
    <div class="user-manage">
      <div class="search-section">
        <div class="search-form">
          <div class="form-item">
            <label>用户名</label>
            <el-input v-model="queryParams.username" placeholder="请输入用户名" clearable @keyup.enter="handleSearch" />
          </div>
          <div class="form-item">
            <label>昵称</label>
            <el-input v-model="queryParams.name" placeholder="请输入昵称" clearable @keyup.enter="handleSearch" />
          </div>
          <div class="form-item">
            <label>状态</label>
            <el-select v-model="queryParams.status" placeholder="全部状态" clearable>
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
          <div class="form-item">
            <label>权限</label>
            <el-select v-model="queryParams.role" placeholder="全部权限" clearable>
              <el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
          <div class="form-item">
            <label>认证</label>
            <el-select v-model="queryParams.professional" placeholder="全部" clearable>
              <el-option label="认证" :value="true" />
              <el-option label="未认证" :value="false" />
            </el-select>
          </div>
          <div class="form-item">
            <label>包含注销</label>
            <el-switch v-model="queryParams.includeDeleted" active-text="是" inactive-text="否" @change="handleSearch" />
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

      <div class="toolbar">
        <div class="left-actions">
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增用户</el-button>
          <el-button type="danger" :icon="Delete" :disabled="selectedRows.length === 0" @click="handleBatchDelete">
            批量删除
          </el-button>
        </div>
        <div class="right-info">共 <span class="highlight">{{ total }}</span> 条记录</div>
      </div>

      <div class="table-section">
        <el-table
          :data="tableData"
          v-loading="loading"
          row-key="id"
          stripe
          class="user-table"
          :row-class-name="getRowClassName"
          @selection-change="handleSelectionChange"
          @row-click="handleViewDetail"
        >
          <el-table-column type="selection" width="55" align="center" :selectable="(row: UserVO) => canManage(row)" />
          <el-table-column label="头像" width="70" align="center">
            <template #default="{ row }">
              <img
                v-if="row.avatar"
                :src="row.avatar"
                referrerpolicy="no-referrer"
                class="user-avatar-img"
                style="display:block;margin:0 auto"
                @error="console.error('头像加载失败:', row.avatar)"
              />
              <el-avatar v-else :size="40" :icon="UserFilled" class="user-avatar" />
            </template>
          </el-table-column>
          <el-table-column prop="username" label="用户名" min-width="110" align="center" />
          <el-table-column prop="name" label="昵称" min-width="90" align="center" />
          <el-table-column label="权限" width="100" align="center">
            <template #default="{ row }"><el-tag size="small" effect="dark">{{ getRoleLabel(row.role) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="状态" width="85" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="getStatusType(row)" effect="dark">{{ getStatusLabel(row) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="level" label="等级" width="70" align="center" />
          <el-table-column prop="safety" label="安全等级" width="85" align="center" />
          <el-table-column prop="fanCount" label="粉丝数" width="80" align="center" />
          <el-table-column prop="songCount" label="歌曲数" width="80" align="center" />
          <el-table-column label="认证" width="65" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.professional" size="small" type="success">认证</el-tag>
              <el-tag v-else size="small" type="info">未认证</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="loginTime" label="最后登录" min-width="160" align="center">
            <template #default="{ row }">{{ formatDate(row.loginTime) }}</template>
          </el-table-column>
          <el-table-column prop="updateTime" label="修改时间" min-width="160" align="center">
            <template #default="{ row }">{{ formatDate(row.updateTime) }}</template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" min-width="160" align="center">
            <template #default="{ row }">{{ formatDate(row.createTime) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="{ row }">
              <template v-if="canManage(row)">
                <el-button type="primary" link :icon="Edit" @click.stop="handleEdit(row)">编辑</el-button>
                <el-button v-if="!row.isDeleted" type="warning" link :icon="CircleClose" @click.stop="handleCancel(row)">注销</el-button>
                <el-button type="danger" link :icon="Delete" @click.stop="handleDelete(row)">删除</el-button>
              </template>
              <el-tag v-else size="small" type="info">无权限</el-tag>
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

      <el-dialog v-model="detailDialogVisible" title="用户详情" width="720px" class="user-dialog detail-dialog">
        <div v-if="currentUser" class="detail-body">
          <!-- 基本信息区域 -->
          <div class="detail-section">
            <div class="section-title">基本信息</div>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">用户名</span>
                <span class="detail-value">{{ currentUser.username }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">昵称</span>
                <span class="detail-value">{{ currentUser.name || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">角色</span>
                <el-tag size="small" effect="dark">{{ getRoleLabel(currentUser.role) }}</el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">性别</span>
                <span class="detail-value">{{ getGenderLabel(currentUser.gender) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">状态</span>
                <el-tag size="small" :type="getStatusType(currentUser)" effect="dark">{{ getStatusLabel(currentUser) }}</el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">认证</span>
                <el-tag v-if="currentUser.professional" size="small" type="success">认证</el-tag>
                <el-tag v-else size="small" type="info">未认证</el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">出生年月</span>
                <span class="detail-value">{{ currentUser.birth || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">居住地</span>
                <span class="detail-value">{{ currentUser.city || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 等级与数据区域 -->
          <div class="detail-section">
            <div class="section-title">等级与数据</div>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">等级</span>
                <span class="detail-value highlight-level">Lv.{{ currentUser.level }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">经验值</span>
                <span class="detail-value">{{ currentUser.exp }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">安全等级</span>
                <span class="detail-value">{{ currentUser.safety }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">粉丝数</span>
                <span class="detail-value">{{ currentUser.fanCount }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">关注数</span>
                <span class="detail-value">{{ currentUser.followCount }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">点赞数</span>
                <span class="detail-value">{{ currentUser.likeCount }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">歌曲数</span>
                <span class="detail-value">{{ currentUser.songCount }}</span>
              </div>
            </div>
          </div>

          <!-- 头像与简介区域 -->
          <div class="detail-section">
            <div class="section-title">头像与简介</div>
            <div class="avatar-desc-area">
              <img
                v-if="currentUser.avatar"
                :src="currentUser.avatar"
                referrerpolicy="no-referrer"
                class="detail-avatar-img"
                style="display:block"
                @error="console.error('头像加载失败:', currentUser.avatar)"
              />
              <el-avatar v-else :size="80" :icon="UserFilled" class="detail-avatar" />
              <div class="detail-desc">
                <div class="detail-label">个人简介</div>
                <div class="detail-value desc-text">{{ currentUser.description || '暂无简介' }}</div>
              </div>
            </div>
          </div>

          <!-- 情绪标签区域 -->
          <div class="detail-section" v-if="currentUser.emoTags && currentUser.emoTags.length > 0">
            <div class="section-title">情绪标签</div>
            <div class="tags-area">
              <el-tag v-for="tag in currentUser.emoTags" :key="tag" size="small" class="detail-tag">{{ tag }}</el-tag>
            </div>
          </div>

          <!-- 兴趣标签区域 -->
          <div class="detail-section" v-if="currentUser.interestTags && currentUser.interestTags.length > 0">
            <div class="section-title">兴趣标签</div>
            <div class="tags-area">
              <el-tag v-for="tag in currentUser.interestTags" :key="tag" size="small" class="detail-tag">{{ tag }}</el-tag>
            </div>
          </div>

          <!-- 时间信息区域 -->
          <div class="detail-section">
            <div class="section-title">时间信息</div>
            <div class="detail-grid time-grid">
              <div class="detail-item">
                <span class="detail-label">最后登录</span>
                <span class="detail-value">{{ formatDate(currentUser.loginTime) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">修改时间</span>
                <span class="detail-value">{{ formatDate(currentUser.updateTime) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">创建时间</span>
                <span class="detail-value">{{ formatDate(currentUser.createTime) }}</span>
              </div>
            </div>
          </div>
        </div>
        <template #footer>
          <el-button @click="handleCloseDetail">关闭</el-button>
          <el-button v-if="currentUser && canManage(currentUser)" type="primary" @click="handleEditCurrentUser">编辑</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="dialogVisible" :title="dialogTitle" width="620px" class="user-dialog">
        <el-form ref="formRef" :model="formData" :rules="rules" label-width="96px" class="user-form">
          <el-row :gutter="16">
            <el-col :span="12"><el-form-item label="用户名" prop="username"><el-input v-model="formData.username" /></el-form-item></el-col>
            <el-col :span="12">
              <el-form-item v-if="!isEdit" label="密码" prop="password"><el-input v-model="formData.password" show-password /></el-form-item>
              <el-form-item v-else label="密码" prop="password"><el-input v-model="formData.password" placeholder="不修改请留空" show-password clearable /></el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="昵称"><el-input v-model="formData.name" /></el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="权限">
                <el-select v-model="formData.role" style="width: 100%">
                  <el-option v-for="item in availableRoleOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="性别">
                <el-select v-model="formData.gender" style="width: 100%">
                  <el-option v-for="item in genderOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="状态">
                <el-select v-model="formData.status" style="width: 100%">
                  <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="经验值">
                <el-input-number v-model="formData.exp" :min="0" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="出生年月">
                <el-date-picker v-model="formData.birth" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="居住地">
                <el-input v-model="formData.city" placeholder="请输入城市" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="认证">
                <el-switch v-model="formData.professional" active-text="认证" inactive-text="未认证" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="头像">
            <div class="avatar-edit">
              <img
                v-if="avatarDisplaySrc"
                :src="avatarDisplaySrc"
                referrerpolicy="no-referrer"
                class="edit-avatar-img"
                style="display:block;flex-shrink:0"
                @error="console.error('头像预览加载失败:', avatarDisplaySrc)"
              />
              <el-avatar v-else :size="64" :icon="UserFilled" />
              <input
                ref="avatarFileInputRef"
                type="file"
                accept="image/*"
                class="avatar-file-input"
                @change="onAvatarFileSelected"
              />
              <el-button type="primary" plain @click="openAvatarPicker">选择图片</el-button>
              <el-button v-if="hasPendingAvatarFile" link type="danger" @click="clearAvatarSelection">移除所选图片</el-button>
              <span v-else class="avatar-hint">选择后仅在点击「确定」时上传至 OSS</span>
            </div>
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入简介" />
          </el-form-item>
          <!-- 情绪标签 -->
          <el-form-item label="情绪标签">
            <div class="tags-edit">
              <el-tag v-for="tag in formData.emoTags" :key="tag" closable class="edit-tag" @close="handleEmoTagClose(tag)">{{ tag }}</el-tag>
              <el-input
                v-if="emoTagInputVisible"
                ref="emoTagInputRef"
                v-model="emoTagInputValue"
                size="small"
                class="tag-input"
                @keyup.enter="handleEmoTagConfirm"
                @blur="handleEmoTagConfirm"
              />
              <el-button v-else size="small" class="tag-add-btn" @click="showEmoTagInput">+ 添加标签</el-button>
            </div>
          </el-form-item>

          <!-- 兴趣标签 -->
          <el-form-item label="兴趣标签">
            <div class="tags-edit">
              <el-tag v-for="tag in formData.interestTags" :key="tag" closable class="edit-tag" @close="handleInterestTagClose(tag)">{{ tag }}</el-tag>
              <el-input
                v-if="interestTagInputVisible"
                ref="interestTagInputRef"
                v-model="interestTagInputValue"
                size="small"
                class="tag-input"
                @keyup.enter="handleInterestTagConfirm"
                @blur="handleInterestTagConfirm"
              />
              <el-button v-else size="small" class="tag-add-btn" @click="showInterestTagInput">+ 添加标签</el-button>
            </div>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </template>
      </el-dialog>
    </div>
  </AppLayout>
</template>

<style scoped src="../../styles/common.css"></style>
<style scoped src="./user-manage.css"></style>
