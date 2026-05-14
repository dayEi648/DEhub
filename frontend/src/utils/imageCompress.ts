/**
 * 使用 Canvas API 压缩图片
 * @param file 原始图片文件
 * @param maxWidth 最大宽度（默认 1024）
 * @param maxHeight 最大高度（默认 1024）
 * @param maxSizeBytes 目标最大字节数（默认 2MB）
 * @param initialQuality 初始压缩质量（默认 0.92）
 * @returns 压缩后的 File 对象（格式统一为 image/jpeg）
 */
export function compressImage(
  file: File,
  maxWidth: number = 1024,
  maxHeight: number = 1024,
  maxSizeBytes: number = 2 * 1024 * 1024,
  initialQuality: number = 0.92
): Promise<File> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        // 根据 EXIF 方向调整尺寸计算（Canvas 绘制会自动处理，但宽高需交换）
        let { width, height } = img

        // 等比缩放至限定尺寸内
        if (width > maxWidth || height > maxHeight) {
          const ratio = Math.min(maxWidth / width, maxHeight / height)
          width = Math.round(width * ratio)
          height = Math.round(height * ratio)
        }

        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('无法创建 canvas 上下文'))
          return
        }
        ctx.drawImage(img, 0, 0, width, height)

        const baseName = file.name.replace(/\.[^.]+$/, '') || 'image'

        // 递归尝试不同质量，直到满足大小限制或降至最低质量
        const tryCompress = (quality: number) => {
          canvas.toBlob(
            (blob) => {
              if (!blob) {
                reject(new Error('图片压缩失败'))
                return
              }
              if (blob.size <= maxSizeBytes || quality <= 0.3) {
                const compressedFile = new File([blob], `${baseName}.jpg`, {
                  type: 'image/jpeg',
                  lastModified: Date.now()
                })
                resolve(compressedFile)
              } else {
                tryCompress(Math.max(quality - 0.08, 0.3))
              }
            },
            'image/jpeg',
            quality
          )
        }

        tryCompress(initialQuality)
      }
      img.onerror = () => reject(new Error('图片加载失败'))
      img.src = e.target?.result as string
    }
    reader.onerror = () => reject(new Error('文件读取失败'))
    reader.readAsDataURL(file)
  })
}
