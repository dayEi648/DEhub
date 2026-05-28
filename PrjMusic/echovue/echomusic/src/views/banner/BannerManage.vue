<script setup lang="ts">
import { Delete, Edit, Plus, Top, Bottom } from '@element-plus/icons-vue'
import AppLayout from '@/components/Layout/AppLayout.vue'
import { useBannerManage } from './useBannerManage'

const {
  tableData,
  loading,
  dialogVisible,
  dialogTitle,
  isEdit,
  formRef,
  formData,
  rules,
  targetSearchLoading,
  targetSearchOptions,
  selectedTarget,
  previewCoverUrl,
  MAX_BANNER_COUNT,
  handleAdd,
  handleEdit,
  handleDelete,
  handleSubmit,
  handleTargetTypeChange,
  searchTargets,
  selectTarget,
  moveUp,
  moveDown
} = useBannerManage()
</script>

<template>
  <AppLayout title="推送管理" :breadcrumb="['系统管理', '推送管理']">
    <div class="manage-page banner-manage">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="left-actions">
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增推送</el-button>
        </div>
        <div class="right-info">
          当前 <span class="highlight">{{ tableData.length }}</span> / {{ MAX_BANNER_COUNT }} 张
        </div>
      </div>

      <!-- 表格区域 -->
      <div class="table-section">
        <el-table :data="tableData" v-loading="loading" stripe row-key="id" class="banner-table">
          <el-table-column type="index" label="序号" width="60" align="center" />
          <el-table-column label="封面" width="90" align="center">
            <template #default="{ row }">
              <img v-if="row.coverUrl" :src="row.coverUrl" class="banner-thumb" alt="cover" />
              <div v-else class="banner-thumb-placeholder">无图</div>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" min-width="120" show-overflow-tooltip />
          <el-table-column prop="description" label="简述" min-width="160" show-overflow-tooltip />
          <el-table-column label="类型" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.targetType === 'MUSIC' ? 'primary' : 'success'" effect="dark">
                {{ row.targetType === 'MUSIC' ? '音乐' : '专辑' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="targetName" label="目标" min-width="120" show-overflow-tooltip />
          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row, $index }">
              <el-button link :icon="Top" :disabled="$index === 0" @click="moveUp($index)">上移</el-button>
              <el-button link :icon="Bottom" :disabled="$index === tableData.length - 1" @click="moveDown($index)">下移</el-button>
              <el-button type="primary" link :icon="Edit" @click="handleEdit(row)">编辑</el-button>
              <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && tableData.length === 0" description="暂无推送数据" :image-size="80" />
      </div>

      <!-- 新增/编辑弹窗 -->
      <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" class="dialog">
        <el-form ref="formRef" :model="formData" :rules="rules" label-width="88px" class="form">
          <el-form-item label="目标类型" prop="targetType">
            <el-radio-group v-model="formData.targetType" @change="handleTargetTypeChange">
              <el-radio label="MUSIC">音乐</el-radio>
              <el-radio label="ALBUM">专辑</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="选择目标" prop="targetId">
            <el-select
              v-model="selectedTarget"
              value-key="id"
              filterable
              remote
              reserve-keyword
              placeholder="输入名称搜索"
              :remote-method="searchTargets"
              :loading="targetSearchLoading"
              style="width: 100%"
              clearable
              @change="selectTarget"
            >
              <el-option
                v-for="opt in targetSearchOptions"
                :key="opt.id"
                :label="opt.label"
                :value="opt"
              />
            </el-select>
          </el-form-item>

          <el-form-item v-if="previewCoverUrl" label="封面预览">
            <img :src="previewCoverUrl" class="preview-cover" alt="preview" />
          </el-form-item>

          <el-form-item label="推图标题" prop="title">
            <el-input v-model="formData.title" placeholder="请输入推图标题" maxlength="50" show-word-limit />
          </el-form-item>

          <el-form-item label="推图简述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入推图简述"
              maxlength="120"
              show-word-limit
            />
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
<style scoped src="./banner-manage.css"></style>
