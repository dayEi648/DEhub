import { onMounted, reactive, ref, toRef, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { addMusic, deleteMusics, getMusicPage, updateMusic } from '@/api/music'
import type { MusicSavePayload } from '@/api/music'
import { getUserById, getUserPage } from '@/api/user'
import { searchAlbums } from '@/api/album'
import type { MusicDTO, MusicPageQuery, MusicVO } from '@/types/music'
import { useTagInput } from '@/composables/useTagInput'

export function useMusicManage() {
  // 查询参数
  const queryParams = reactive<MusicPageQuery>({
    pageNum: 1,
    pageSize: 10,
    musicName: '',
    style: '',
    vip: undefined,
    albumId: undefined,
    isRecommended: undefined,
    isDeleted: undefined,
    sortBy: 'create_time',
    sortOrder: 'desc'
  })

  // 表格数据
  const tableData = ref<MusicVO[]>([])
  const total = ref(0)
  const loading = ref(false)
  const selectedRows = ref<MusicVO[]>([])

  // 弹窗状态
  const dialogVisible = ref(false)
  const detailDialogVisible = ref(false)
  const dialogTitle = ref('新增音乐')
  const isEdit = ref(false)
  const formRef = ref()
  const currentMusic = ref<MusicVO | null>(null)

  // 表单数据
  const formData = reactive<MusicDTO>({
    musicName: '',
    authorIds: [],
    albumId: undefined,
    vip: false,
    emoTags: [],
    interestTags: [],
    source: '',
    style: '',
    hot: 0,
    isRecommended: false,
    fileUrl: '',
    lyricsUrl: '',
    image1Url: '',
    image2Url: '',
    image3Url: '',
    languages: [],
    instruments: [],
    releaseDate: ''
  })

  // 标签输入逻辑（使用通用 composable）
  const emoTagsInput = useTagInput(toRef(formData, 'emoTags'))
  const interestTagsInput = useTagInput(toRef(formData, 'interestTags'))
  const langsInput = useTagInput(toRef(formData, 'languages'))
  const instrumentsInput = useTagInput(toRef(formData, 'instruments'))

  /** 本地待提交文件；仅在点击「确定」时随 multipart 上传 */
  const pendingMusicFiles = reactive({
    file: null as File | null,
    lyricsFile: null as File | null,
    image1File: null as File | null,
    image2File: null as File | null,
    image3File: null as File | null
  })

  const refMusicAudio = ref<HTMLInputElement | null>(null)
  const refMusicLyrics = ref<HTMLInputElement | null>(null)
  const refMusicImg1 = ref<HTMLInputElement | null>(null)
  const refMusicImg2 = ref<HTMLInputElement | null>(null)
  const refMusicImg3 = ref<HTMLInputElement | null>(null)

  function clearPendingMusicFiles() {
    pendingMusicFiles.file = null
    pendingMusicFiles.lyricsFile = null
    pendingMusicFiles.image1File = null
    pendingMusicFiles.image2File = null
    pendingMusicFiles.image3File = null
  }

  type PendingKey = keyof typeof pendingMusicFiles

  function onPendingMusicFileChange(key: PendingKey, e: Event) {
    const input = e.target as HTMLInputElement
    const f = input.files?.[0] ?? null
    pendingMusicFiles[key] = f
    input.value = ''
  }

  function openMusicFilePicker(which: 'audio' | 'lyrics' | 'img1' | 'img2' | 'img3') {
    const map = {
      audio: refMusicAudio,
      lyrics: refMusicLyrics,
      img1: refMusicImg1,
      img2: refMusicImg2,
      img3: refMusicImg3
    }
    map[which].value?.click()
  }

  // 用户缓存：ID -> 昵称
  const userCache = ref<Map<number, string>>(new Map())
  // 正在加载的用户ID集合
  const loadingUsers = ref<Set<number>>(new Set())
  // 当前编辑/详情中的作者名称映射
  const authorNames = ref<Map<string, string>>(new Map())
  // 已废弃：原ID输入方式
  const newAuthorId = ref<number | undefined>(undefined)

  // 作者搜索相关
  const selectedAuthor = ref<{ id: number; name: string; username: string } | null>(null)
  const authorSearchLoading = ref(false)
  const authorSearchOptions = ref<Array<{ id: number; name: string; username: string }>>([])

  // 专辑搜索相关
  const albumSearchKeyword = ref('')
  const albumSearchLoading = ref(false)
  const albumSearchOptions = ref<Array<{ id: number; albumName: string }>>([])
  const selectedAlbum = ref<{ id: number; albumName: string } | null>(null)

  /** 列表筛选条：与弹窗专辑选择独立，避免互相覆盖 */
  const queryAlbumSearchLoading = ref(false)
  const queryAlbumSearchOptions = ref<Array<{ id: number; albumName: string }>>([])
  const selectedQueryAlbum = ref<{ id: number; albumName: string } | null>(null)

  // 表单验证规则
  const rules = {
    musicName: [{ required: true, message: '请输入音乐名称', trigger: 'blur' }]
  }

  // 批量查询用户昵称
  const fetchUserNames = async (userIds: number[]) => {
    const uniqueIds = userIds.filter(id => !userCache.value.has(id) && !loadingUsers.value.has(id))

    for (const id of uniqueIds) {
      loadingUsers.value.add(id)
      try {
        const user = await getUserById(id)
        userCache.value.set(id, user.name || user.username || `用户${id}`)
      } catch (error) {
        userCache.value.set(id, `用户${id}`)
      } finally {
        loadingUsers.value.delete(id)
      }
    }
  }

  // 获取作者昵称显示（用于表格）
  const getAuthorNames = (authorIds?: number[]): string => {
    if (!authorIds || authorIds.length === 0) return '-'
    return authorIds.map(id => userCache.value.get(id) || `用户${id}`).join('  ')
  }

  // 加载数据
  const loadData = async () => {
    loading.value = true
    try {
      const res = await getMusicPage(queryParams)
      tableData.value = res.records.map(item => ({
        ...item,
        normalStatus: !item.isDeleted
      }))
      total.value = res.total

      // 收集所有作者ID并查询昵称
      const allAuthorIds: number[] = []
      res.records.forEach(item => {
        if (item.authorIds) {
          allAuthorIds.push(...item.authorIds)
        }
      })
      if (allAuthorIds.length > 0) {
        await fetchUserNames([...new Set(allAuthorIds)])
      }
    } finally {
      loading.value = false
    }
  }

  // 重置表单
  const resetForm = () => {
    clearPendingMusicFiles()
    formData.id = undefined
    formData.musicName = ''
    formData.authorIds = []
    formData.albumId = undefined
    formData.vip = false
    formData.emoTags = []
    formData.interestTags = []
    formData.source = ''
    formData.style = ''
    formData.hot = 0
    formData.isRecommended = false
    formData.fileUrl = ''
    formData.lyricsUrl = ''
    formData.image1Url = ''
    formData.image2Url = ''
    formData.image3Url = ''
    formData.languages = []
    formData.instruments = []
    formData.releaseDate = ''
    newAuthorId.value = undefined
    authorNames.value.clear()
    selectedAuthor.value = null
    authorSearchOptions.value = []
    albumSearchKeyword.value = ''
    albumSearchLoading.value = false
    albumSearchOptions.value = []
    selectedAlbum.value = null
  }

  // 新增
  const handleAdd = () => {
    isEdit.value = false
    dialogTitle.value = '新增音乐'
    resetForm()
    dialogVisible.value = true
  }

  // 编辑
  const handleEdit = async (row: MusicVO) => {
    isEdit.value = true
    dialogTitle.value = '编辑音乐'
    clearPendingMusicFiles()
    Object.assign(formData, row)
    formData.authorIds = row.authorIds?.map(String) || []

    // 同步重置专辑选择状态，防止上次编辑的 selectedAlbum 污染本次
    if (row.albumId && row.albumId > 0) {
      selectedAlbum.value = {
        id: row.albumId,
        albumName: row.albumName || `专辑ID: ${row.albumId}`
      }
    } else {
      selectedAlbum.value = null
    }
    albumSearchKeyword.value = ''
    albumSearchOptions.value = []

    // 查询当前音乐的作者昵称
    authorNames.value.clear()
    if (row.authorIds && row.authorIds.length > 0) {
      await fetchUserNames(row.authorIds)
      row.authorIds.forEach(id => {
        authorNames.value.set(String(id), userCache.value.get(id) || `用户${id}`)
      })
    }

    dialogVisible.value = true
  }

  // 查看详情
  const handleViewDetail = async (row: MusicVO) => {
    currentMusic.value = row
    // 查询作者昵称
    authorNames.value.clear()
    if (row.authorIds && row.authorIds.length > 0) {
      await fetchUserNames(row.authorIds)
      row.authorIds.forEach(id => {
        authorNames.value.set(String(id), userCache.value.get(id) || `用户${id}`)
      })
    }
    detailDialogVisible.value = true
  }

  // 关闭详情
  const handleCloseDetail = () => {
    detailDialogVisible.value = false
    currentMusic.value = null
  }

  // 从详情编辑
  const handleEditCurrentMusic = () => {
    if (currentMusic.value) {
      detailDialogVisible.value = false
      handleEdit(currentMusic.value)
    }
  }

  // 删除
  const handleDelete = (row: MusicVO) => {
    ElMessageBox.confirm(`确认删除音乐 "${row.musicName}" 吗？`, '删除确认', { type: 'warning' })
      .then(async () => {
        await deleteMusics([row.id])
        ElMessage.success('删除成功')
        loadData()
      })
      .catch(() => {})
  }

  // 批量删除
  const handleBatchDelete = () => {
    if (!selectedRows.value.length) {
      ElMessage.warning('请选择要删除的数据')
      return
    }
    ElMessageBox.confirm(`确认删除 ${selectedRows.value.length} 条音乐记录吗？`, '批量删除确认', { type: 'warning' })
      .then(async () => {
        await deleteMusics(selectedRows.value.map((item) => item.id))
        ElMessage.success('批量删除成功')
        loadData()
      })
      .catch(() => {})
  }

  // 提交
  const handleSubmit = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid: boolean) => {
      if (!valid) return
      const payload: MusicSavePayload = {
        ...formData,
        file: pendingMusicFiles.file ?? undefined,
        lyricsFile: pendingMusicFiles.lyricsFile ?? undefined,
        image1File: pendingMusicFiles.image1File ?? undefined,
        image2File: pendingMusicFiles.image2File ?? undefined,
        image3File: pendingMusicFiles.image3File ?? undefined
      }
      if (isEdit.value) {
        await updateMusic(payload)
      } else {
        await addMusic(payload)
      }
      ElMessage.success(isEdit.value ? '修改成功' : '新增成功')
      clearPendingMusicFiles()
      dialogVisible.value = false
      loadData()
    })
  }

  watch(dialogVisible, (open) => {
    if (!open) {
      clearPendingMusicFiles()
    }
  })

  // 搜索
  const handleSearch = () => {
    queryParams.pageNum = 1
    loadData()
  }

  // 重置
  const handleReset = () => {
    queryParams.musicName = ''
    queryParams.style = ''
    queryParams.vip = undefined
    queryParams.albumId = undefined
    queryParams.isRecommended = undefined
    queryParams.isDeleted = undefined
    queryParams.pageNum = 1
    queryParams.pageSize = 10
    queryParams.sortBy = 'create_time'
    queryParams.sortOrder = 'desc'
    selectedQueryAlbum.value = null
    queryAlbumSearchOptions.value = []
    loadData()
  }

  // 排序变更
  const handleSortChange = () => {
    queryParams.pageNum = 1
    loadData()
  }

  // 选择变更
  const handleSelectionChange = (selection: MusicVO[]) => {
    selectedRows.value = selection
  }

  // 分页变更
  const handlePageChange = (page: number) => {
    queryParams.pageNum = page
    loadData()
  }

  // 每页条数变更
  const handleSizeChange = (size: number) => {
    queryParams.pageSize = size
    queryParams.pageNum = 1
    loadData()
  }

  // 切换推荐状态
  const handleToggleRecommend = async (row: MusicVO) => {
    try {
      await updateMusic({
        id: row.id,
        musicName: row.musicName,
        isRecommended: row.isRecommended
      })
      ElMessage.success(row.isRecommended ? '已设为推荐' : '已取消推荐')
      loadData()
    } catch (error) {
      ElMessage.error('操作失败')
      row.isRecommended = !row.isRecommended
    }
  }

  // 切换状态（删除/恢复）
  const handleToggleStatus = async (row: MusicVO & { normalStatus?: boolean }) => {
    const isDeleted = !row.normalStatus
    try {
      await updateMusic({
        id: row.id,
        musicName: row.musicName,
        isDeleted: isDeleted
      })
      ElMessage.success(isDeleted ? '已移至回收站' : '已恢复正常')
      loadData()
    } catch (error) {
      ElMessage.error('操作失败')
      row.normalStatus = !row.normalStatus
    }
  }

  // 格式化日期
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  // 远程搜索专辑
  const searchAlbumList = async (query: string) => {
    if (!query || query.trim().length === 0) {
      albumSearchOptions.value = []
      return
    }
    albumSearchLoading.value = true
    try {
      albumSearchOptions.value = await searchAlbums(query.trim(), 10)
    } catch {
      albumSearchOptions.value = []
    } finally {
      albumSearchLoading.value = false
    }
  }

  /** 列表筛选：按专辑名模糊查专辑表 */
  const searchAlbumListForQuery = async (query: string) => {
    if (!query || query.trim().length === 0) {
      queryAlbumSearchOptions.value = []
      return
    }
    queryAlbumSearchLoading.value = true
    try {
      queryAlbumSearchOptions.value = await searchAlbums(query.trim(), 10)
    } catch {
      queryAlbumSearchOptions.value = []
    } finally {
      queryAlbumSearchLoading.value = false
    }
  }

  const onQueryAlbumChange = (album: { id: number; albumName: string } | null | undefined) => {
    if (!album) {
      queryParams.albumId = undefined
      selectedQueryAlbum.value = null
      queryAlbumSearchOptions.value = []
      return
    }
    queryParams.albumId = album.id
    selectedQueryAlbum.value = album
    queryAlbumSearchOptions.value = []
  }

  // 选择专辑
  const selectAlbum = (album?: { id: number; albumName: string } | null) => {
    if (!album) return
    formData.albumId = album.id
    selectedAlbum.value = album
    albumSearchKeyword.value = ''
    albumSearchOptions.value = []
  }

  // 清除专辑选择
  const clearAlbumSelection = () => {
    formData.albumId = -1
    selectedAlbum.value = null
    albumSearchKeyword.value = ''
    albumSearchOptions.value = []
  }

  // 远程搜索作者
  const searchAuthors = async (query: string) => {
    if (!query || query.trim().length === 0) {
      authorSearchOptions.value = []
      return
    }
    authorSearchLoading.value = true
    try {
      const res = await getUserPage({
        name: query.trim(),
        pageNum: 1,
        pageSize: 5
      })
      authorSearchOptions.value = (res.records || []).map((u) => ({
        id: u.id,
        name: u.name ?? u.username ?? '',
        username: u.username
      }))
    } catch (error) {
      authorSearchOptions.value = []
    } finally {
      authorSearchLoading.value = false
    }
  }

  // 添加作者（通过选择用户对象）
  const addAuthor = (user: { id: number; name: string; username: string } | null) => {
    if (!user || !user.id) return
    if (!formData.authorIds) {
      formData.authorIds = []
    }
    const idStr = String(user.id)
    if (formData.authorIds.includes(idStr)) {
      ElMessage.warning('该作者已存在')
      selectedAuthor.value = null
      return
    }
    formData.authorIds.push(idStr)
    // 更新缓存和显示名称
    const displayName = user.name || user.username || `用户${user.id}`
    userCache.value.set(user.id, displayName)
    authorNames.value.set(idStr, displayName)
    // 清空搜索
    selectedAuthor.value = null
    authorSearchOptions.value = []
    ElMessage.success('添加成功')
  }

  // 添加作者ID（原方法保留兼容）
  const addAuthorId = async () => {
    if (!newAuthorId.value) {
      ElMessage.warning('请输入作者ID')
      return
    }
    if (!formData.authorIds) {
      formData.authorIds = []
    }
    const idStr = String(newAuthorId.value)
    if (formData.authorIds.includes(idStr)) {
      ElMessage.warning('该作者已存在')
      return
    }
    formData.authorIds.push(idStr)
    // 查询作者昵称
    if (!userCache.value.has(newAuthorId.value)) {
      await fetchUserNames([newAuthorId.value])
    }
    authorNames.value.set(idStr, userCache.value.get(newAuthorId.value) || `用户${newAuthorId.value}`)
    newAuthorId.value = undefined
    ElMessage.success('添加成功')
  }

  // 移除作者ID
  const removeAuthorId = (id: string) => {
    if (!formData.authorIds) return
    const index = formData.authorIds.indexOf(id)
    if (index > -1) {
      formData.authorIds.splice(index, 1)
      authorNames.value.delete(id)
      ElMessage.success('移除成功')
    }
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
    formRef,
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
    clearPendingMusicFiles,
    newAuthorId,
    userCache,
    authorNames,
    rules,
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
    // 专辑搜索相关
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
    // 作者搜索相关
    selectedAuthor,
    authorSearchLoading,
    authorSearchOptions,
    searchAuthors,
    addAuthor,
    // 情绪标签输入
    emoTagInputVisible: emoTagsInput.inputVisible,
    emoTagInputValue: emoTagsInput.inputValue,
    emoTagInputRef: emoTagsInput.inputRef,
    showEmoTagInput: emoTagsInput.showInput,
    handleEmoTagConfirm: emoTagsInput.handleConfirm,
    handleEmoTagClose: emoTagsInput.handleClose,
    // 兴趣标签输入
    interestTagInputVisible: interestTagsInput.inputVisible,
    interestTagInputValue: interestTagsInput.inputValue,
    interestTagInputRef: interestTagsInput.inputRef,
    showInterestTagInput: interestTagsInput.showInput,
    handleInterestTagConfirm: interestTagsInput.handleConfirm,
    handleInterestTagClose: interestTagsInput.handleClose,
    langInputVisible: langsInput.inputVisible,
    langInputValue: langsInput.inputValue,
    langInputRef: langsInput.inputRef,
    showLangInput: langsInput.showInput,
    handleLangConfirm: langsInput.handleConfirm,
    handleLangClose: langsInput.handleClose,
    instrumentInputVisible: instrumentsInput.inputVisible,
    instrumentInputValue: instrumentsInput.inputValue,
    instrumentInputRef: instrumentsInput.inputRef,
    showInstrumentInput: instrumentsInput.showInput,
    handleInstrumentConfirm: instrumentsInput.handleConfirm,
    handleInstrumentClose: instrumentsInput.handleClose
  }
}
