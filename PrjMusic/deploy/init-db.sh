#!/bin/bash
# =============================================================================
# EchoMemory 数据库初始化脚本
# 按正确依赖顺序执行 SqlsCopy/*.txt 建表脚本
# =============================================================================
set -e

# 可通过环境变量传入，默认值为本地开发配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_PASS="${DB_PASS:-}"
DB_NAME="${DB_NAME:-echomusic}"

# SQL 文件所在目录
SQL_DIR="${SQL_DIR:-/opt/echomemory/SqlsCopy}"

export PGPASSWORD="$DB_PASS"

# 辅助函数：按通配符查找并执行 SQL 文件
run_sql() {
    local pattern="$1"
    local file
    file=$(find "$SQL_DIR" -maxdepth 1 -type f -iname "$pattern" | head -n1)
    if [ -n "$file" ]; then
        echo "  -> $(basename "$file")"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$file"
    else
        echo "  -> WARN: 未找到匹配 '$pattern' 的文件，已跳过"
    fi
}

echo "=========================================="
echo "  EchoMemory 数据库初始化"
echo "  目标: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo "=========================================="

# -----------------------------------------------------------------------------
# [1/6] 安装必要扩展 + 创建通用函数
# -----------------------------------------------------------------------------
echo ""
echo "[1/6] 安装扩展并创建通用函数..."
echo "  -> CREATE EXTENSION pg_trgm (模糊查询索引依赖)"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" || true
echo "  -> 创建 update_modified_column() 函数"
run_sql "common_trigger_function.txt"

# -----------------------------------------------------------------------------
# [2/6] 创建基础表（无相互依赖，可并行概念上但这里串行执行）
# -----------------------------------------------------------------------------
echo ""
echo "[2/6] 创建基础表..."
for tbl in users albums playlists comments hot daily_stats notifications private_msgs space_posts; do
    run_sql "$tbl.txt"
done

# -----------------------------------------------------------------------------
# [3/6] 创建 musics 表（被关系触发器引用，但自身无前置依赖）
# -----------------------------------------------------------------------------
echo ""
echo "[3/6] 创建 musics 表..."
run_sql "musics.txt"

# play_history 外键依赖 musics 和 users，必须在两者之后创建
echo "  -> play_history.txt"
run_sql "play_history.txt"

# -----------------------------------------------------------------------------
# [4/6] 创建 AI 相关表（ai_sessions 外键依赖 users 表）
# -----------------------------------------------------------------------------
echo ""
echo "[4/6] 创建 AI 表..."
run_sql "ai_sessions.txt"
run_sql "ai_messages.txt"
run_sql "ai_recommend_logs.txt"

# -----------------------------------------------------------------------------
# [5/6] 创建关系触发器（依赖 musics / albums / users 已存在）
# -----------------------------------------------------------------------------
echo ""
echo "[5/6] 创建关系触发器..."
run_sql "musics_albums_trigger.txt"
run_sql "musics_users_trigger.txt"

# -----------------------------------------------------------------------------
# [6/6] 初始化 echovector 向量库
# -----------------------------------------------------------------------------
echo ""
echo "[6/6] 初始化 echovector 库（pgvector + kb_documents）..."
# 先确保库存在且已安装 pgvector 扩展
echo "  -> 确保 echovector 库存在..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'echovector'" | grep -q 1 || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE echovector;"

echo "  -> 安装 pgvector 扩展..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d echovector -c "CREATE EXTENSION IF NOT EXISTS vector;" || true

echo "  -> 导入 kb_documents 向量表..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d echovector -f /opt/echomemory/deploy/init-echovector.sql

# -----------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  数据库初始化完成！"
echo "=========================================="
echo ""
echo "已创建的库:"
echo "  - $DB_NAME"
echo "  - echovector"
echo ""
echo "验证命令:"
echo "  docker exec -it echomemory-postgres psql -U $DB_USER -d $DB_NAME -c '\\dt'"
