import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { ConversationResponse, MessageResponse } from '@/types'
import * as chatApi from '@/api/chat'
import { useUiStore } from './ui'

export const useChatStore = defineStore('chat', () => {
  const uiStore = useUiStore()

  const conversations = ref<ConversationResponse[]>([])
  const currentMessages = ref<MessageResponse[]>([])
  const currentConversationId = ref<number | null>(null)
  const isLoading = ref(false)
  const totalConversations = ref(0)

  async function fetchConversations(params?: { skip?: number; limit?: number }) {
    const { data } = await chatApi.fetchConversations(params)
    conversations.value = data.items
    totalConversations.value = data.total
    return data
  }

  async function fetchMessages(conversationId: number, params?: { skip?: number; limit?: number }) {
    const { data } = await chatApi.fetchMessages(conversationId, params)
    currentMessages.value = data
    currentConversationId.value = conversationId
    return data
  }

  async function deleteConversation(id: number) {
    await chatApi.deleteConversation(id)
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (currentConversationId.value === id) {
      currentConversationId.value = null
      currentMessages.value = []
    }
    uiStore.showToast('对话已删除', 'success')
  }

  async function sendMessage(userInput: string, conversationId?: number) {
    // Optimistic user message
    const userMessage: MessageResponse = {
      id: Date.now(),
      conversation_id: conversationId || 0,
      role: 'user',
      content: userInput,
      created_at: new Date().toISOString()
    }
    currentMessages.value.push(userMessage)

    // Placeholder assistant message
    const assistantMessage: MessageResponse = {
      id: Date.now() + 1,
      conversation_id: conversationId || 0,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    }
    currentMessages.value.push(assistantMessage)

    isLoading.value = true

    try {
      const { data } = await chatApi.sendMessage({
        conversation_id: conversationId,
        user_input: userInput
      })

      assistantMessage.content = data.response

      if (data.conversation_id) {
        const cid = data.conversation_id
        currentConversationId.value = cid
        userMessage.conversation_id = cid
        assistantMessage.conversation_id = cid
      }

      if (!conversationId) {
        await fetchConversations()
      }
    } catch (err: any) {
      assistantMessage.content += '\n[发生错误]'
      uiStore.showToast(err.message || '对话异常', 'error')
    } finally {
      isLoading.value = false
    }
  }

  return {
    conversations,
    currentMessages,
    currentConversationId,
    isLoading,
    totalConversations,
    fetchConversations,
    fetchMessages,
    deleteConversation,
    sendMessage
  }
})
