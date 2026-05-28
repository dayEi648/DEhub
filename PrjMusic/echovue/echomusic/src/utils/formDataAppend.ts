/**
 * Multipart 下同一 key 的重复字段：若数组为空则 forEach 不会 append，
 * Spring 绑定为 null，后端无法把标签清空为「空数组」。
 * 空数组时 append 一个空串，后端再过滤空白得到空列表。
 */
export function appendStringArrayForMultipart(
  fd: FormData,
  key: string,
  arr: string[] | undefined | null
): void {
  if (arr == null) return
  if (arr.length === 0) {
    fd.append(key, '')
  } else {
    arr.forEach((t) => fd.append(key, t))
  }
}
