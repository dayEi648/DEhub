/** 用户名：3–32，字母数字下划线与中文，无空格 */
const USERNAME_PATTERN = /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/

/** 可见 ASCII + 常用全角与中文（密码可含标点）；禁止不可见控制符 */
const PASSWORD_DISALLOWED = /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/

export function validateUsername(value: string): string | true {
  const s = value.trim()
  if (!s) return '请输入用户名'
  if (s.length < 3 || s.length > 32) return '用户名长度为 3～32 个字符'
  if (!USERNAME_PATTERN.test(s)) return '仅支持中文、字母、数字与下划线'
  return true
}

export function validatePassword(value: string): string | true {
  if (!value) return '请输入密码'
  if (value.length < 8 || value.length > 64) return '密码长度为 8～64 位'
  if (PASSWORD_DISALLOWED.test(value)) return '密码不能包含不可见控制字符'
  if (!/[a-zA-Z]/.test(value) || !/[0-9]/.test(value)) return '密码需同时包含字母与数字'
  return true
}

/** 昵称可选；填写时 1～32，允许空格与间隔号 */
export function validateNickname(value: string): string | true {
  const s = value.trim()
  if (!s) return true
  if (s.length > 32) return '昵称最多 32 个字符'
  if (!/^[\u4e00-\u9fa5a-zA-Z0-9_\s·•]+$/.test(s)) return '昵称含非法字符'
  return true
}
