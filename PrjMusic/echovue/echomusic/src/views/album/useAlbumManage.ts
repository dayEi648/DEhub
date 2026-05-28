import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAlbumPage,
  addAlbum,
  updateAlbum,
  deleteAlbums,
  cancelAlbum,
  restoreAlbum
} from '@/api/album'
import { getMusicsByIds } from '@/api/music'
import type { AlbumVO, AlbumDTO, AlbumPageQuery } from '@/types/album'
import type { AlbumSavePayload } from '@/api/album'
import type { MusicVO } from '@/types/music'

export function useAlbumManage() {
  // 查询参数
  const queryParams = reactive<AlbumPageQuery>({
    pageNum: 1,
    pageSize: 10,
    albumName: '',
    authorName: '',
    isRecommended: undefined,
    isDeleted: undefined,
    sortBy: 'create_time',
    sortOrder: 'desc'
  })

  const tableData = ref<AlbumVO[]>([])
  const total = ref(0)
  const loading = ref(false)
  const selectedRows = ref<AlbumVO[]>([])

  const dialogVisible = ref(false)
  const detailDialogVisible = ref(false)
  const dialogTitle = ref('新增专辑')
  const isEdit = ref(false)
  const currentAlbum = ref<AlbumVO | null>(null)

  const formData = reactive<AlbumDTO & { emoTags: string[]; interestTags: string[] }>({
    albumName: '',
    authorIds: [],
    authorNames: [],
    albumDescription: '',
    source: '',
    emoTags: [],
    interestTags: [],
    image1Url: '',
    image2Url: '',
    songIds: [],
    isRecommended: false
  })

  /** 已关联歌曲详情（只读展示曲名，不在此页增删歌曲） */
  const addedSongs = ref<Map<number, MusicVO>>(new Map())

  // 图片文件
  const image1File = ref<File | null>(null)
  const image1PreviewUrl = ref('')
  const image2File = ref<File | null>(null)
  const image2PreviewUrl = ref('')

  const image1FileInputRef = ref<HTMLInputElement | null>(null)
  const image2FileInputRef = ref<HTMLInputElement | null>(null)

  function revokePreview(urlRef: typeof image1PreviewUrl) {
    if (urlRef.value && urlRef.value.startsWith('blob:')) {
      URL.revokeObjectURL(urlRef.value)
      urlRef.value = ''
    }
  }

  function onImageFileSelected(index: 1 | 2, e: Event) {
    const input = e.target as HTMLInputElement
    const file = input.files?.[0]
    if (!file) return
    if (index === 1) {
      revokePreview(image1PreviewUrl)
      image1File.value = file
      image1PreviewUrl.value = URL.createObjectURL(file)
    } else {
      revokePreview(image2PreviewUrl)
      image2File.value = file
      image2PreviewUrl.value = URL.createObjectURL(file)
    }
    input.value = ''
  }

  function clearImageSelection(index: 1 | 2) {
    if (index === 1) {
      revokePreview(image1PreviewUrl)
      image1File.value = null
    } else {
      revokePreview(image2PreviewUrl)
      image2File.value = null
    }
  }

  function openImagePicker(index: 1 | 2) {
    if (index === 1) image1FileInputRef.value?.click()
    else image2FileInputRef.value?.click()
  }

  // 表单
  const rules = {
    albumName: [
      { required: true, message: '请输入专辑名称', trigger: 'blur' },
      { max: 32, message: '最长 32 个字符', trigger: 'blur' }
    ]
  }
  const formRef = ref()

  const loadData = async () => {
    loading.value = true
    try {
      const res = await getAlbumPage(queryParams)
      tableData.value = res.records
      total.value = res.total
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  const handleSearch = () => {
    queryParams.pageNum = 1
    loadData()
  }

  const handleReset = () => {
    queryParams.albumName = ''
    queryParams.authorName = ''
    queryParams.isRecommended = undefined
    queryParams.isDeleted = undefined
    queryParams.pageNum = 1
    queryParams.pageSize = 10
    queryParams.sortBy = 'create_time'
    queryParams.sortOrder = 'desc'
    loadData()
  }

  const handlePageChange = (page: number) => {
    queryParams.pageNum = page
    loadData()
  }
  const handleSizeChange = (size: number) => {
    queryParams.pageSize = size
    queryParams.pageNum = 1
    loadData()
  }
  const handleSortChange = () => {
    loadData()
  }
  const handleSelectionChange = (selection: AlbumVO[]) => {
    selectedRows.value = selection
  }

  function resetForm() {
    formData.id = undefined
    formData.albumName = ''
    formData.authorIds = []
    formData.authorNames = []
    formData.albumDescription = ''
    formData.source = ''
    formData.emoTags = []
    formData.interestTags = []
    formData.image1Url = ''
    formData.image2Url = ''
    formData.songIds = []
    formData.isRecommended = false
    clearImageSelection(1)
    clearImageSelection(2)
    addedSongs.value = new Map()
    if (formRef.value) formRef.value.resetFields()
  }

  const handleAdd = () => {
    isEdit.value = false
    dialogTitle.value = '新增专辑'
    resetForm()
    dialogVisible.value = true
  }

  const handleEdit = async (row: AlbumVO) => {
    isEdit.value = true
    dialogTitle.value = '编辑专辑'
    resetForm()
    Object.assign(formData, {
      id: row.id,
      albumName: row.albumName,
      authorIds: row.authorIds ? [...row.authorIds] : [],
      authorNames: row.authorNames ? [...row.authorNames] : [],
      albumDescription: row.albumDescription || '',
      source: row.source || '',
      emoTags: row.emoTags ? [...row.emoTags] : [],
      interestTags: row.interestTags ? [...row.interestTags] : [],
      image1Url: row.image1Url || '',
      image2Url: row.image2Url || '',
      songIds: row.songIds ? [...row.songIds] : [],
      isRecommended: row.isRecommended ?? false
    })

    // 加载已关联歌曲详情（仅用于展示曲名）
    if (row.songIds && row.songIds.length > 0) {
      try {
        const musics = await getMusicsByIds(row.songIds)
        for (const m of musics) {
          addedSongs.value.set(m.id, m)
        }
      } catch {
        // 仅展示 songIds，曲名回退为 getAddedSongName
      }
    }

    dialogVisible.value = true
  }

  const handleSubmit = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid: boolean) => {
      if (!valid) return
      try {
        const payload: AlbumSavePayload = {
          ...formData,
          image1File: image1File.value ?? undefined,
          image2File: image2File.value ?? undefined
        }
        if (isEdit.value) {
          const { songIds: _sid, authorIds: _aid, emoTags: _e, interestTags: _i, ...updateBody } = payload
          await updateAlbum(updateBody)
          ElMessage.success('修改成功')
        } else {
          await addAlbum(payload)
          ElMessage.success('新增成功')
        }
        clearImageSelection(1)
        clearImageSelection(2)
        dialogVisible.value = false
        loadData()
      } catch (error) {
        console.error('提交失败:', error)
      }
    })
  }

  watch(dialogVisible, (open) => {
    if (!open) {
      clearImageSelection(1)
      clearImageSelection(2)
    }
  })

  const handleDelete = (row: AlbumVO) => {
    ElMessageBox.confirm(`确定要删除专辑 "${row.albumName}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
      .then(async () => {
        await deleteAlbums([row.id])
        ElMessage.success('删除成功')
        loadData()
      })
      .catch(() => {})
  }

  /** targetIsDeleted：开关切换后的目标状态（与 el-switch @change 新值一致；true=下架，false=上架） */
  const handleToggleStatus = async (row: AlbumVO, targetIsDeleted: boolean) => {
    try {
      if (targetIsDeleted) {
        await cancelAlbum(row.id)
        ElMessage.success('下架成功')
      } else {
        await restoreAlbum(row.id)
        ElMessage.success('上架成功')
      }
      loadData()
    } catch (error) {
      console.error('状态切换失败:', error)
    }
  }

  const handleBatchDelete = () => {
    if (selectedRows.value.length === 0) {
      ElMessage.warning('请选择要删除的专辑')
      return
    }
    ElMessageBox.confirm(`确定要删除选中的 ${selectedRows.value.length} 个专辑吗？`, '确认批量删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
      .then(async () => {
        const ids = selectedRows.value.map((row) => row.id)
        await deleteAlbums(ids)
        ElMessage.success('批量删除成功')
        loadData()
      })
      .catch(() => {})
  }

  const handleViewDetail = (row: AlbumVO, column: unknown, event: Event) => {
    const target = event.target as HTMLElement
    const isCheckbox = target.closest('.el-checkbox') || target.closest('.el-table-column--selection')
    const isButton = target.closest('button') || target.closest('.el-button')
    const isSwitch = target.closest('.el-switch')
    const isActionColumn = (column as { label?: string } | undefined)?.label === '操作'
    const isStatusColumn = (column as { label?: string } | undefined)?.label === '状态'
    if (isCheckbox || isButton || isActionColumn || isSwitch || isStatusColumn) return
    currentAlbum.value = row
    detailDialogVisible.value = true
  }

  const handleCloseDetail = () => {
    detailDialogVisible.value = false
    currentAlbum.value = null
  }

  const handleEditCurrentAlbum = () => {
    if (!currentAlbum.value) return
    const album = currentAlbum.value
    handleCloseDetail()
    handleEdit(album)
  }

  const getAddedSongName = (id: number): string => {
    return addedSongs.value.get(id)?.musicName || `歌曲${id}`
  }

  const getRowClassName = ({ row }: { row: AlbumVO }): string => {
    if (row.isDeleted) {
      return 'deleted-row'
    }
    return ''
  }

  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  onMounted(() => {
    loadData()
  })

  return {
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
    image1File,
    image1PreviewUrl,
    image2File,
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
  }
}
