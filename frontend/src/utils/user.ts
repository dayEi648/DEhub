/**
 * 用户相关工具函数
 */

export const PERMISSION_MAP: Record<number, { label: string; labelEn: string; color: string }> = {
  0: { label: '普通用户', labelEn: 'MEMBER', color: '#7FE6EF' },
  1: { label: '管理员', labelEn: 'ADMIN', color: '#F5A623' },
  2: { label: '超级管理员', labelEn: 'SUPER ADMIN', color: '#FFE52C' },
};

/**
 * 获取权限信息（文本、颜色等）
 * @param permission 权限值 0|1|2
 */
export function getPermissionInfo(permission: number) {
  return PERMISSION_MAP[permission] ?? PERMISSION_MAP[0];
}

/**
 * 格式化日期为中文本地化字符串
 * @param date ISO 日期字符串
 * @param fallback 无效日期时的回退文本
 */
export function formatDate(date: string | undefined | null, fallback = '----'): string {
  if (!date) return fallback;
  try {
    return new Date(date).toLocaleDateString('zh-CN');
  } catch {
    return fallback;
  }
}
