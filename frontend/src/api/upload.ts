import request from '../utils/request'

/**
 * 上传图片到 OSS
 * @param file 图片文件
 * @param scene 上传场景，默认 generic
 * @returns 返回包含 OSS URL 的对象
 */
export function uploadImage(file: File, scene: string = 'generic') {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<{ url: string }>(`/uploads/image?scene=${encodeURIComponent(scene)}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
