import { ref, reactive, onMounted, nextTick, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserPage, addUser, updateUser, deleteUsers, cancelUser } from '@/api/user'
import type { UserVO, UserDTO, UserPageQuery } from '@/types/user'
import { statusOptions, genderOptions, roleOptions, UserRole } from '@/types/user'
import { getUser } from '@/utils/authStorage'

export function useUserManage() {
  const currentLoginUser = computed(() => getUser())
  const currentUserRole = computed(() => currentLoginUser.value?.role ?? UserRole.USER)

  /** 当前登录用户是否可管理目标用户 */
  const canManage = (row: UserVO): boolean => {
    const myRole = currentUserRole.value
    const targetRole = row.role ?? UserRole.USER
    // 超级管理员可管理所有人；普通管理员只能管理 role <= 1 的用户
    return myRole >= UserRole.SUPER_ADMIN || (myRole === UserRole.ADMIN && targetRole <= UserRole.VIP)
  }

  const queryParams = reactive<UserPageQuery>({
    pageNum: 1,
    pageSize: 10,
    username: '',
    name: '',
    status: undefined,
    role: undefined,
    professional: undefined,
    includeDeleted: false,
    sortBy: 'create_time',
    sortOrder: 'desc'
  })

  const tableData = ref<UserVO[]>([])
  const total = ref(0)
  const loading = ref(false)
  const selectedRows = ref<UserVO[]>([])

  const dialogVisible = ref(false)
  const dialogTitle = ref('')
  const isEdit = ref(false)

  const detailDialogVisible = ref(false)
  const currentUser = ref<UserVO | null>(null)

  const formData = reactive<UserDTO & { emoTags: string[]; interestTags: string[] }>({
    username: '',
    password: '',
    name: '',
    role: 0,
    gender: 0,
    status: 0,
    exp: 0,
    avatar: '',
    city: '',
    description: '',
    birth: '',
    professional: false,
    emoTags: [],
    interestTags: []
  })

  /** 仅在点击「确定」时随 multipart 提交；取消关闭弹窗不会上传 */
  const avatarFile = ref<File | null>(null)
  const avatarPreviewObjectUrl = ref('')

  const avatarDisplaySrc = computed(() => {
    if (avatarPreviewObjectUrl.value) {
      return avatarPreviewObjectUrl.value
    }
    return formData.avatar || undefined
  })

  const hasPendingAvatarFile = computed(() => avatarFile.value != null)

  function revokeAvatarPreview() {
    if (avatarPreviewObjectUrl.value) {
      URL.revokeObjectURL(avatarPreviewObjectUrl.value)
      avatarPreviewObjectUrl.value = ''
    }
  }

  function onAvatarFileSelected(e: Event) {
    const input = e.target as HTMLInputElement
    const file = input.files?.[0]
    if (!file) {
      return
    }
    revokeAvatarPreview()
    avatarFile.value = file
    avatarPreviewObjectUrl.value = URL.createObjectURL(file)
    input.value = ''
  }

  function clearAvatarSelection() {
    revokeAvatarPreview()
    avatarFile.value = null
  }

  const avatarFileInputRef = ref<HTMLInputElement | null>(null)

  function openAvatarPicker() {
    avatarFileInputRef.value?.click()
  }

  const emoTagInputVisible = ref(false)
  const emoTagInputValue = ref('')
  const emoTagInputRef = ref()
  const interestTagInputVisible = ref(false)
  const interestTagInputValue = ref('')
  const interestTagInputRef = ref()

  const rules = {
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
    ],
    password: [
      {
        validator: (_: unknown, value: string, cb: (e?: Error) => void) => {
          if (!isEdit.value) {
            if (!value || value.length < 6) {
              cb(new Error('请输入密码（6～20 位）'))
              return
            }
            if (value.length > 20) {
              cb(new Error('长度在 6 到 20 个字符'))
              return
            }
          } else if (value && value.length > 0) {
            if (value.length < 6 || value.length > 20) {
              cb(new Error('长度在 6 到 20 个字符'))
              return
            }
          }
          cb()
        },
        trigger: 'blur'
      }
    ],
    name: [{ max: 50, message: '最多 50 个字符', trigger: 'blur' }],
    exp: [{ type: 'number', min: 0, message: '经验值不能小于 0', trigger: 'blur' }]
  }

  const formRef = ref()

  const showEmoTagInput = () => {
    emoTagInputVisible.value = true
    nextTick(() => {
      emoTagInputRef.value?.focus()
    })
  }

  const handleEmoTagConfirm = () => {
    if (emoTagInputValue.value) {
      if (!formData.emoTags) {
        formData.emoTags = []
      }
      if (!formData.emoTags.includes(emoTagInputValue.value)) {
        formData.emoTags.push(emoTagInputValue.value)
      }
    }
    emoTagInputVisible.value = false
    emoTagInputValue.value = ''
  }

  const handleEmoTagClose = (tag: string) => {
    formData.emoTags = formData.emoTags.filter((t) => t !== tag)
  }

  const showInterestTagInput = () => {
    interestTagInputVisible.value = true
    nextTick(() => {
      interestTagInputRef.value?.focus()
    })
  }

  const handleInterestTagConfirm = () => {
    if (interestTagInputValue.value) {
      if (!formData.interestTags) {
        formData.interestTags = []
      }
      if (!formData.interestTags.includes(interestTagInputValue.value)) {
        formData.interestTags.push(interestTagInputValue.value)
      }
    }
    interestTagInputVisible.value = false
    interestTagInputValue.value = ''
  }

  const handleInterestTagClose = (tag: string) => {
    formData.interestTags = formData.interestTags.filter((t) => t !== tag)
  }

  const loadData = async () => {
    loading.value = true
    try {
      const res = await getUserPage(queryParams)
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
    queryParams.username = ''
    queryParams.name = ''
    queryParams.status = undefined
    queryParams.role = undefined
    queryParams.professional = undefined
    queryParams.includeDeleted = false
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

  const handleSelectionChange = (selection: UserVO[]) => {
    selectedRows.value = selection
  }

  const handleAdd = () => {
    isEdit.value = false
    dialogTitle.value = '新增用户'
    resetForm()
    dialogVisible.value = true
  }

  const handleEdit = (row: UserVO) => {
    if (!canManage(row)) {
      ElMessage.warning('您没有权限编辑该用户')
      return
    }
    isEdit.value = true
    dialogTitle.value = '编辑用户'
    clearAvatarSelection()
    formData.password = ''
    Object.assign(formData, {
      id: row.id,
      username: row.username,
      name: row.name,
      role: row.role,
      gender: row.gender,
      status: row.status,
      exp: row.exp,
      avatar: row.avatar,
      city: row.city,
      description: row.description,
      birth: row.birth,
      professional: row.professional,
      emoTags: row.emoTags ? [...row.emoTags] : [],
      interestTags: row.interestTags ? [...row.interestTags] : []
    })
    emoTagInputVisible.value = false
    emoTagInputValue.value = ''
    interestTagInputVisible.value = false
    interestTagInputValue.value = ''
    dialogVisible.value = true
  }

  const resetForm = () => {
    clearAvatarSelection()
    formData.id = undefined
    formData.username = ''
    formData.password = ''
    formData.name = ''
    formData.role = 0
    formData.gender = 0
    formData.status = 0
    formData.exp = 0
    formData.avatar = ''
    formData.city = ''
    formData.description = ''
    formData.birth = ''
    formData.professional = false
    formData.emoTags = []
    formData.interestTags = []
    emoTagInputVisible.value = false
    emoTagInputValue.value = ''
    interestTagInputVisible.value = false
    interestTagInputValue.value = ''
    if (formRef.value) {
      formRef.value.resetFields()
    }
  }

  const handleSubmit = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid: boolean) => {
      if (!valid) return
      try {
        const payload = {
          ...formData,
          avatarFile: avatarFile.value ?? undefined
        }
        if (isEdit.value) {
          await updateUser(payload)
          ElMessage.success('修改成功')
        } else {
          await addUser(payload)
          ElMessage.success('新增成功')
        }
        clearAvatarSelection()
        dialogVisible.value = false
        loadData()
      } catch (error) {
        console.error('提交失败:', error)
      }
    })
  }

  watch(dialogVisible, (open) => {
    if (!open) {
      clearAvatarSelection()
    }
  })

  const handleCancel = (row: UserVO) => {
    if (!canManage(row)) {
      ElMessage.warning('您没有权限注销该用户')
      return
    }
    ElMessageBox.confirm(`确定要注销用户 "${row.username}" 吗？注销后该账号将无法登录，但数据会被保留。`, '确认注销', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
      .then(async () => {
        await cancelUser(row.id)
        ElMessage.success('注销成功')
        loadData()
      })
      .catch(() => {})
  }

  const handleDelete = (row: UserVO) => {
    if (!canManage(row)) {
      ElMessage.warning('您没有权限删除该用户')
      return
    }
    ElMessageBox.confirm(`确定要永久删除用户 "${row.username}" 吗？此操作不可恢复！`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    })
      .then(async () => {
        await deleteUsers([row.id])
        ElMessage.success('删除成功')
        loadData()
      })
      .catch(() => {})
  }

  const handleBatchDelete = () => {
    if (selectedRows.value.length === 0) {
      ElMessage.warning('请选择要删除的用户')
      return
    }
    const manageable = selectedRows.value.filter(canManage)
    const unmanageableCount = selectedRows.value.length - manageable.length
    if (manageable.length === 0) {
      ElMessage.warning('选中的用户均没有权限删除')
      return
    }
    if (unmanageableCount > 0) {
      ElMessage.warning(`已过滤 ${unmanageableCount} 个无权限删除的用户`)
    }
    ElMessageBox.confirm(`确定要删除选中的 ${manageable.length} 个用户吗？`, '确认批量删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
      .then(async () => {
        const ids = manageable.map((row) => row.id)
        await deleteUsers(ids)
        ElMessage.success('批量删除成功')
        loadData()
      })
      .catch(() => {})
  }

  const getStatusType = (row?: { status?: number; isDeleted?: boolean }): string => {
    if (row?.isDeleted) return 'info'
    const option = statusOptions.find((opt) => opt.value === row?.status)
    return option?.type || 'info'
  }

  const getStatusLabel = (row?: { status?: number; isDeleted?: boolean }): string => {
    if (row?.isDeleted) return '注销'
    const option = statusOptions.find((opt) => opt.value === row?.status)
    return option?.label || '未知'
  }

  const getGenderLabel = (gender?: number): string => {
    const option = genderOptions.find((opt) => opt.value === gender)
    return option?.label || '未知'
  }

  const getRoleLabel = (role?: number): string => {
    const option = roleOptions.find((opt) => opt.value === role)
    return option?.label || '未知'
  }

  const getRowClassName = ({ row }: { row: UserVO }): string => {
    if (row.isDeleted) {
      return 'deleted-row'
    }
    return ''
  }

  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  }

  const handleViewDetail = (row: UserVO, column: unknown, event: Event) => {
    const target = event.target as HTMLElement
    const isCheckbox = target.closest('.el-checkbox') || target.closest('.el-table-column--selection')
    const isButton = target.closest('button') || target.closest('.el-button')
    const isActionColumn = (column as { label?: string } | undefined)?.label === '操作'
    if (isCheckbox || isButton || isActionColumn) {
      return
    }
    currentUser.value = row
    detailDialogVisible.value = true
  }

  const handleCloseDetail = () => {
    detailDialogVisible.value = false
    currentUser.value = null
  }

  const handleEditCurrentUser = () => {
    if (!currentUser.value) return
    const user = currentUser.value
    if (!canManage(user)) {
      ElMessage.warning('您没有权限编辑该用户')
      return
    }
    handleCloseDetail()
    handleEdit(user)
  }

  /** 根据当前登录角色过滤可供选择的角色选项 */
  const availableRoleOptions = computed(() => {
    const myRole = currentUserRole.value
    if (myRole >= UserRole.SUPER_ADMIN) {
      return roleOptions
    }
    // 普通管理员只能给用户分配普通用户或 VIP 角色
    return roleOptions.filter((opt) => opt.value <= UserRole.VIP)
  })

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
    currentUserRole,
    canManage,
    availableRoleOptions
  }
}
