"""
直接启动 FastAPI 服务器的脚本。
使用字符串形式让 uvicorn 自行导入模块。
"""
import sys
from pathlib import Path

# 将脚本所在目录加入 PYTHONPATH，确保无论在哪里运行都能导入 app 模块
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="debug")
