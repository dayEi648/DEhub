import { get, post, del } from '@/utils/request'
import type {
  SpacePostVO,
  SpacePostDTO,
  SpacePostForwardDTO,
  SpacePostPageQuery
} from '@/types/spacePost'
import type { PageDataVo } from '@/types/user'

/**
 * 分页查询空间说说
 */
export function getSpacePostPage(
  params: SpacePostPageQuery
): Promise<PageDataVo<SpacePostVO>> {
  return get('/space-posts/page', params)
}

/**
 * 发表说说
 */
export function addSpacePost(data: SpacePostDTO): Promise<void> {
  return post('/space-posts', data)
}

/**
 * 点赞/取消点赞说说
 */
export function likeSpacePost(id: number): Promise<void> {
  return post(`/space-posts/${id}/like`)
}

/**
 * 转发说说
 */
export function forwardSpacePost(data: SpacePostForwardDTO): Promise<void> {
  return post('/space-posts/forward', data)
}

/**
 * 删除说说
 */
export function deleteSpacePost(id: number): Promise<void> {
  return del(`/space-posts/${id}`)
}
