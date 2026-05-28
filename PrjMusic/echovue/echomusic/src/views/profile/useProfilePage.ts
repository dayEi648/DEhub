import { ref } from 'vue'
import type { ProfileTab } from '@/components/ProfileLayout/ProfileLayout.vue'

export function useProfilePage() {
  const activeTab = ref<ProfileTab>('favorites')

  return {
    activeTab
  }
}
