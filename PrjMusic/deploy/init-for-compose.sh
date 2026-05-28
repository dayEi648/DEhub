#!/bin/bash
# =============================================================================
# EchoMemory 数据库初始化脚本（Docker Compose 专用）
# =============================================================================
# 特点：
#   - 幂等设计（CREATE DATABASE IF NOT EXISTS 等）
#   - 使用 Docker 服务名 "postgres" 连接
#   - 在 Docker 容器内执行，依赖 pgvector/pgvector:pg16 镜像
# =============================================================================
set -e

# 环境变量（由 docker-compose 注入）
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-dehub}"
DB_PASS="${DB_PASSWORD:-}"
SQL_DIR="${SQL_DIR:-/sqls}"

echo "=========================================="
echo "  EchoMemory 数据库初始化 (Docker)"
echo "  目标: ${DB_USER}@${DB_HOST}:${DB_PORT}"
echo "=========================================="

export PGPASSWORD="${DB_PASS}"

# 辅助函数：按通配符查找并执行 SQL 文件
run_sql() {
    local pattern="$1"
    local target_db="$2"
    local file
    file=$(find "$SQL_DIR" -maxdepth 1 -type f -iname "$pattern" | head -n1)
    if [ -n "$file" ]; then
        echo "  -> $(basename "$file") => ${target_db}"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$target_db" -f "$file"
    else
        echo "  -> WARN: 未找到匹配 '$pattern' 的文件，已跳过"
    fi
}

# 辅助函数：执行单行 SQL
exec_sql() {
    local sql="$1"
    local target_db="${2:-postgres}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$target_db" -c "$sql"
}

# -----------------------------------------------------------------------------
# [1/7] 创建数据库（幂等）
# -----------------------------------------------------------------------------
echo ""
echo "[1/7] 创建数据库（若不存在则跳过）..."
exec_sql "CREATE DATABASE echomusic;" postgres || echo "  -> echomusic 已存在或创建成功"
exec_sql "CREATE DATABASE echovector;" postgres || echo "  -> echovector 已存在或创建成功"

# -----------------------------------------------------------------------------
# [2/7] 安装扩展
# -----------------------------------------------------------------------------
echo ""
echo "[2/7] 安装 PostgreSQL 扩展..."
exec_sql "CREATE EXTENSION IF NOT EXISTS pg_trgm;" echomusic || true
exec_sql "CREATE EXTENSION IF NOT EXISTS vector;" echovector || true

# -----------------------------------------------------------------------------
# [3/7] 创建通用函数
# -----------------------------------------------------------------------------
echo ""
echo "[3/7] 创建通用触发器函数..."
run_sql "common_trigger_function.txt" echomusic

# -----------------------------------------------------------------------------
# [4/7] 创建基础表
# -----------------------------------------------------------------------------
echo ""
echo "[4/7] 创建基础业务表..."
for tbl in users albums playlists comments hot daily_stats notifications private_msgs space_posts; do
    run_sql "$tbl.txt" echomusic
done

# -----------------------------------------------------------------------------
# [5/7] 创建 musics 及其依赖表
# -----------------------------------------------------------------------------
echo ""
echo "[5/7] 创建 musics 与 play_history 表..."
run_sql "musics.txt" echomusic
run_sql "play_history.txt" echomusic

# -----------------------------------------------------------------------------
# [6/7] 创建 AI 相关表与触发器
# -----------------------------------------------------------------------------
echo ""
echo "[6/7] 创建 AI 相关表与关系触发器..."
run_sql "ai_sessions.txt" echomusic
run_sql "ai_messages.txt" echomusic
run_sql "ai_recommend_logs.txt" echomusic
run_sql "musics_albums_trigger.txt" echomusic
run_sql "musics_users_trigger.txt" echomusic

# -----------------------------------------------------------------------------
# [7/7] 初始化 echovector 向量库
# -----------------------------------------------------------------------------
echo ""
echo "[7/7] 初始化 echovector 向量库..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d echovector -f /deploy/init-echovector.sql || true

# -----------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  数据库初始化完成！"
echo "=========================================="
echo ""
echo "已就绪的数据库:"
echo "  - echomusic"
echo "  - echovector"
