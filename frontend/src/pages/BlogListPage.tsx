import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { listBlogPosts } from '../api/blog';
import type { BlogPostListItem, BlogPostQueryParams, BlogPostSortBy } from '../api/types';
import ArchiveHeader from '../components/archive/ArchiveHeader';
import ArchiveSidebar from '../components/archive/ArchiveSidebar';
import FolderCard from '../components/archive/FolderCard';
import Pagination from '../components/ui/Pagination';

const PAGE_SIZE = 12;
type SearchType = 'title' | 'tag';

export default function BlogListPage() {
  const [posts, setPosts] = useState<BlogPostListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState<BlogPostSortBy>('latest');
  const [searchType, setSearchType] = useState<SearchType>('title');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [fetchVersion, setFetchVersion] = useState(0);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params: BlogPostQueryParams = {
        skip: (currentPage - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
        sort_by: sortBy,
      };

      const trimmed = submittedQuery.trim();
      if (trimmed) {
        if (searchType === 'title') {
          params.q = trimmed;
        } else {
          params.tag = trimmed;
        }
      }

      const res = await listBlogPosts(params);
      setPosts(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }, [currentPage, sortBy, searchType, submittedQuery, fetchVersion]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  const handleSearch = (query: string, type: SearchType) => {
    setSubmittedQuery(query);
    setSearchType(type);
    setFetchVersion((v) => v + 1);
    setCurrentPage(1);
  };

  const handleSortChange = (sort: BlogPostSortBy) => {
    setSortBy(sort);
    setCurrentPage(1);
  };

  const hasActiveFilters = submittedQuery.trim() !== '';

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0D0A07' }}>
      {/* 顶部框架 */}
      <header
        className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8"
        style={{
          height: 80,
          background: 'linear-gradient(180deg, #F5A623 0%, #FAA622 50%, #F5A623 100%)',
          borderBottom: '2px solid #1A1612',
        }}
      >
        {/* 螺丝装饰 */}
        <div className="absolute top-2 left-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="absolute top-2 right-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <ArchiveHeader totalFiles={total} />
      </header>

      {/* 左侧边栏 */}
      <aside
        className="fixed left-0 z-40 hidden lg:flex flex-col"
        style={{
          top: 80,
          width: 280,
          height: 'calc(100vh - 120px)',
          background: 'linear-gradient(90deg, #F5A623 0%, #FAA622 50%, #F5A623 100%)',
          borderRight: '2px solid #1A1612',
        }}
      >
        {/* 螺丝装饰 */}
        <div className="absolute bottom-2 left-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="absolute bottom-2 right-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <ArchiveSidebar
          totalFiles={total}
          searchType={searchType}
          sortBy={sortBy}
          onSearch={handleSearch}
          onSortChange={handleSortChange}
        />
      </aside>

      {/* 主内容区域 */}
      <main
        className="flex-1 px-4 sm:px-6 lg:px-8 pb-8"
        style={{
          marginLeft: 0,
          marginTop: 80,
          marginBottom: 40,
        }}
      >
        <div className="lg:ml-[280px]">
          {/* 移动端搜索栏（仅在小屏幕显示） */}
          <div className="lg:hidden mb-4 pt-4">
            <ArchiveSidebar
              totalFiles={total}
              searchType={searchType}
              sortBy={sortBy}
              onSearch={handleSearch}
              onSortChange={handleSortChange}
            />
          </div>

          {/* 搜索结果头部 */}
          {hasActiveFilters && (
            <motion.div
              className="flex items-center gap-3 mb-4 pt-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <span
                className="text-[10px] tracking-[0.3em] font-bold"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                SEARCH RESULTS
              </span>
              <span
                className="text-[10px]"
                style={{ color: '#FFF8EE', opacity: 0.4, fontFamily: 'var(--font-mono)' }}
              >
                {total} 篇档案
              </span>
              <div className="h-px flex-1 bg-[#F5A623]/15" />
            </motion.div>
          )}

          {/* 加载态 */}
          {loading ? (
            <div className="flex items-center justify-center py-24">
              <div className="flex flex-col items-center gap-4">
                <motion.div
                  className="w-10 h-10 border-2 border-[#F5A623] border-t-transparent"
                  style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
                <span
                  className="text-[10px] tracking-wider animate-pulse"
                  style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
                >
                  档案检索中...
                </span>
              </div>
            </div>
          ) : error ? (
            <div className="text-center py-24">
              <p style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }} className="text-sm">
                {error}
              </p>
            </div>
          ) : posts.length === 0 ? (
            <div className="text-center py-24">
              <p
                className="text-base mb-2"
                style={{ color: '#F5A623', opacity: 0.5, fontFamily: 'var(--font-mono)' }}
              >
                EMPTY DRAWER
              </p>
              <p
                className="text-sm"
                style={{ color: '#FFF8EE', opacity: 0.4, fontFamily: 'var(--font-body)' }}
              >
                {hasActiveFilters ? '未找到匹配的档案' : '暂无档案'}
              </p>
            </div>
          ) : (
            <>
              {/* 文件夹网格 */}
              <div className="flex flex-wrap gap-5 pt-4">
                {posts.map((post, index) => (
                  <FolderCard
                    key={post.id}
                    post={post}
                    index={(currentPage - 1) * PAGE_SIZE + index}
                  />
                ))}
              </div>

              {/* 分页 */}
              {total > PAGE_SIZE && (
                <motion.div
                  className="flex justify-center py-10"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                >
                  <Pagination
                    current={currentPage}
                    total={total}
                    pageSize={PAGE_SIZE}
                    onChange={setCurrentPage}
                  />
                </motion.div>
              )}
            </>
          )}

          {/* 底部装饰 */}
          <div className="py-8">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-[#F5A623]/10" />
              <span
                className="text-[9px] tracking-[0.3em] opacity-25"
                style={{ fontFamily: 'var(--font-mono)', color: '#F5A623' }}
              >
                END OF ARCHIVE
              </span>
              <div className="h-px flex-1 bg-[#F5A623]/10" />
            </div>
          </div>
        </div>
      </main>

      {/* 底部框架 */}
      <footer
        className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8"
        style={{
          height: 40,
          background: 'linear-gradient(180deg, #F5A623 0%, #FAA622 50%, #F5A623 100%)',
          borderTop: '2px solid #1A1612',
        }}
      >
        {/* 螺丝装饰 */}
        <div className="absolute top-2 left-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="absolute top-2 right-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          DE hub Documentary Archive
        </span>
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          2026
        </span>
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          SECURE STORAGE
        </span>
      </footer>
    </div>
  );
}
