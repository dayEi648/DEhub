import { ref, computed, watch, toValue, type MaybeRef } from 'vue'
import { getMusicLyrics } from '@/api/music'

export interface LyricLine {
  time: number // 秒
  text: string
}

/**
 * 解析 LRC 歌词文本
 * 支持时间格式：[mm:ss.xx] 和 [mm:ss.xxx]
 * 支持一行多时间标签，如 [00:01.23][00:02.34]歌词
 */
export function parseLrc(lrcText: string): LyricLine[] {
  const lines: LyricLine[] = []
  const timeRegex = /\[(\d{2}):(\d{2})\.(\d{2,3})\]/g

  const rawLines = lrcText.split('\n')

  for (const rawLine of rawLines) {
    const line = rawLine.trim()
    if (!line) continue

    const matches = Array.from(line.matchAll(timeRegex))
    if (matches.length === 0) continue

    // 提取歌词文本（去掉所有时间标签后的剩余部分）
    const text = line.replace(timeRegex, '').trim()
    if (!text) continue

    for (const match of matches) {
      const min = parseInt(match[1] ?? '00', 10)
      const sec = parseInt(match[2] ?? '00', 10)
      const msStr = match[3] ?? '00'
      // 统一转为秒数（两位小数 xxx 表示百分秒，三位小数 xxxx 表示毫秒）
      const ms = msStr.length === 2 ? parseInt(msStr, 10) / 100 : parseInt(msStr, 10) / 1000
      const time = min * 60 + sec + ms
      lines.push({ time, text })
    }
  }

  // 按时间排序
  lines.sort((a, b) => a.time - b.time)

  return lines
}

/**
 * 二分查找当前时间对应的歌词行索引
 * @returns 当前应高亮的行索引，-1 表示还没开始
 */
export function findCurrentLineIndex(lines: LyricLine[], currentTime: number): number {
  if (lines.length === 0) return -1
  if (currentTime < lines[0]!.time) return -1

  let left = 0
  let right = lines.length - 1
  let ans = 0

  while (left <= right) {
    const mid = Math.floor((left + right) / 2)
    if (lines[mid]!.time <= currentTime) {
      ans = mid
      left = mid + 1
    } else {
      right = mid - 1
    }
  }

  return ans
}

/**
 * Composable: 歌词管理
 * @param lyricsUrl 歌词文件 OSS 直链
 * @returns 解析后的歌词行、当前行索引、加载状态
 */
export function useLyrics(musicId: MaybeRef<number | undefined>) {
  const lines = ref<LyricLine[]>([])
  const loading = ref(false)
  const error = ref('')

  async function loadLyrics() {
    const id = toValue(musicId)
    if (!id) {
      lines.value = []
      error.value = ''
      return
    }

    loading.value = true
    error.value = ''
    try {
      const text = await getMusicLyrics(id)
      lines.value = parseLrc(text)
    } catch (e: any) {
      error.value = e?.message || '歌词加载失败'
      lines.value = []
    } finally {
      loading.value = false
    }
  }

  // 监听 ID 变化自动加载
  watch(
    () => toValue(musicId),
    () => loadLyrics(),
    { immediate: true }
  )

  return {
    lines: computed(() => lines.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    findCurrentLineIndex: (currentTime: number) => findCurrentLineIndex(lines.value, currentTime)
  }
}
