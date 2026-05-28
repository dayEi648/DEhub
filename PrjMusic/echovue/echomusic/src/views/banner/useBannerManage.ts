import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getBanners,
  addBanner,
  updateBanner,
  deleteBanner,
  reorderBanner
} from '@/api/banner'
import { searchMusics } from '@/api/album'
import { searchAlbums } from '@/api/album'
import type { BannerVO, BannerSavePayload, BannerTargetType } from '@/types/banner'
import type { MusicVO } from '@/types/music'

const MAX_BANNER_COUNT = 10

interface SearchOption {
  id: number
  label: string
  coverUrl: string
}

export function useBannerManage() {
  const tableData = ref<BannerVO[]>([])
  const loading = ref(false)
  const dialogVisible = ref(false)
  const dialogTitle = ref('新增推送')
  const isEdit = ref(false)
  const editId = ref('')
  const formRef = ref()

  const formData = reactive<BannerSavePayload>({
    title: '',
    description: '',
    targetType: 'MUSIC',
    targetId: 0
  })

  const targetSearchLoading = ref(false)
  const targetSearchOptions = ref<SearchOption[]>([])
  const selectedTarget = ref<SearchOption | null>(null)
  const previewCoverUrl = ref('')

  const rules = {
    title: [{ required: true, message: '请输入推图标题', trigger: 'blur' }],
    description: [{ required: true, message: '请输入推图简述', trigger: 'blur' }],
    targetId: [
      { required: true, message: '请选择目标', trigger: 'change' },
      { validator: (_rule: any, value: number, callback: Function) => {
        if (!value || value <= 0) {
          callback(new Error('请选择目标'))
        } else {
          callback()
        }
      }, trigger: 'change' }
    ]
  }

  const loadData = async () => {
    loading.value = true
    try {
      tableData.value = await getBanners()
    } finally {
      loading.value = false
    }
  }

  const resetForm = () => {
    formData.title = ''
    formData.description = ''
    formData.targetType = 'MUSIC'
    formData.targetId = 0
    selectedTarget.value = null
    targetSearchOptions.value = []
    previewCoverUrl.value = ''
    editId.value = ''
  }

  const handleAdd = () => {
    if (tableData.value.length >= MAX_BANNER_COUNT) {
      ElMessage.warning(`首页轮播推图最多只能有 ${MAX_BANNER_COUNT} 张`)
      return
    }
    isEdit.value = false
    dialogTitle.value = '新增推送'
    resetForm()
    dialogVisible.value = true
  }

  const handleEdit = (row: BannerVO) => {
    isEdit.value = true
    dialogTitle.value = '编辑推送'
    editId.value = row.id
    formData.title = row.title
    formData.description = row.description
    formData.targetType = row.targetType
    formData.targetId = row.targetId
    previewCoverUrl.value = row.coverUrl || ''
    selectedTarget.value = {
      id: row.targetId,
      label: `${row.targetName} (ID: ${row.targetId})`,
      coverUrl: row.coverUrl || ''
    }
    targetSearchOptions.value = [selectedTarget.value]
    dialogVisible.value = true
  }

  const handleDelete = (row: BannerVO) => {
    ElMessageBox.confirm(`确认删除推图 "${row.title}" 吗？`, '删除确认', { type: 'warning' })
      .then(async () => {
        await deleteBanner(row.id)
        ElMessage.success('删除成功')
        loadData()
      })
      .catch(() => {})
  }

  const handleSubmit = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid: boolean) => {
      if (!valid) return
      if (isEdit.value) {
        await updateBanner(editId.value, { ...formData })
        ElMessage.success('修改成功')
      } else {
        await addBanner({ ...formData })
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      resetForm()
      loadData()
    })
  }

  const handleTargetTypeChange = () => {
    formData.targetId = 0
    selectedTarget.value = null
    targetSearchOptions.value = []
    previewCoverUrl.value = ''
  }

  const searchTargets = async (query: string) => {
    if (!query || query.trim().length === 0) {
      targetSearchOptions.value = []
      return
    }
    targetSearchLoading.value = true
    try {
      if (formData.targetType === 'MUSIC') {
        const res = await searchMusics(query.trim(), 10)
        targetSearchOptions.value = (res || []).map((m: MusicVO) => ({
          id: m.id,
          label: `${m.musicName} (ID: ${m.id})`,
          coverUrl: m.image3Url || ''
        }))
      } else {
        const res = await searchAlbums(query.trim(), 10)
        targetSearchOptions.value = (res || []).map((a: { id: number; albumName: string; image2Url?: string }) => ({
          id: a.id,
          label: `${a.albumName} (ID: ${a.id})`,
          coverUrl: a.image2Url || ''
        }))
      }
    } catch {
      targetSearchOptions.value = []
    } finally {
      targetSearchLoading.value = false
    }
  }

  const selectTarget = (option: SearchOption | null) => {
    if (!option) {
      formData.targetId = 0
      previewCoverUrl.value = ''
      return
    }
    formData.targetId = option.id
    previewCoverUrl.value = option.coverUrl
  }

  const moveUp = async (index: number) => {
    if (index <= 0) return
    const ids = tableData.value.map(b => b.id)
    const temp = ids[index]!
    ids[index] = ids[index - 1]!
    ids[index - 1] = temp
    await reorderBanner(ids)
    ElMessage.success('上移成功')
    loadData()
  }

  const moveDown = async (index: number) => {
    if (index >= tableData.value.length - 1) return
    const ids = tableData.value.map(b => b.id)
    const temp = ids[index]!
    ids[index] = ids[index + 1]!
    ids[index + 1] = temp
    await reorderBanner(ids)
    ElMessage.success('下移成功')
    loadData()
  }

  onMounted(() => {
    loadData()
  })

  return {
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
    loadData,
    handleAdd,
    handleEdit,
    handleDelete,
    handleSubmit,
    handleTargetTypeChange,
    searchTargets,
    selectTarget,
    moveUp,
    moveDown
  }
}
