import { nextTick, type Ref, ref } from 'vue'

/**
 * 标签输入通用逻辑（需传入 reactive 字段的 toRef，以便删除时写回数组）
 */
export function useTagInput(listRef: Ref<string[] | undefined>) {
  const inputVisible = ref(false)
  const inputValue = ref('')
  const inputRef = ref()

  const showInput = () => {
    inputVisible.value = true
    nextTick(() => {
      inputRef.value?.focus()
    })
  }

  const handleConfirm = () => {
    if (inputValue.value) {
      if (!listRef.value) {
        listRef.value = []
      }
      if (!listRef.value.includes(inputValue.value)) {
        listRef.value.push(inputValue.value)
      }
    }
    inputVisible.value = false
    inputValue.value = ''
  }

  const handleClose = (tag: string) => {
    if (listRef.value) {
      listRef.value = listRef.value.filter((t) => t !== tag)
    }
  }

  return {
    inputVisible,
    inputValue,
    inputRef,
    showInput,
    handleConfirm,
    handleClose
  }
}
