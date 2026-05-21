import request from '../utils/request'
import type {
  ForumPostListResponse,
  ForumPostListParams,
  ForumZone,
} from '../types/forum'

export function getForumPostList(params: ForumPostListParams = {}) {
  return request.get<ForumPostListResponse>('/forum_posts/', { params })
}

export function getForumZoneList() {
  return request.get<ForumZone[]>('/forum_zones/')
}
