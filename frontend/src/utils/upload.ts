/**
 * 图片上传公共工具
 * 提供统一的文件校验、预览生成等能力
 */

/** 前端允许的最大图片大小：20MB */
export const MAX_IMAGE_SIZE = 20 * 1024 * 1024

/** 允许的图片 MIME 类型 */
export const ALLOWED_IMAGE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
]

/**
 * 校验图片文件是否合法
 * @param file 待校验的文件
 * @returns 错误信息字符串；合法则返回 null
 */
export function validateImageFile(file: File): string | null {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return '仅支持 JPG、PNG、WebP 格式的图片'
  }
  if (file.size > MAX_IMAGE_SIZE) {
    return '图片大小不能超过 20MB'
  }
  return null
}

/**
 * 使用 FileReader 生成图片文件的 base64 预览 URL
 * @param file 图片文件
 * @returns Promise<base64 URL>
 */
export function createImagePreview(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('图片预览生成失败'))
    reader.readAsDataURL(file)
  })
}
