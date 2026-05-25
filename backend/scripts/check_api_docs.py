import argparse
import re
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
ROUTE_PATTERN = re.compile(
    r"(?im)^\s{0,3}#{1,6}\s+`?(GET|POST|PUT|PATCH|DELETE)`?\s+`?([^`\s]+)`?"
)


def collect_documented_routes(docs_dir: Path) -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for doc_path in docs_dir.glob("*.md"):
        text = doc_path.read_text(encoding="utf-8")
        for method, path in ROUTE_PATTERN.findall(text):
            routes.add((method.upper(), path.strip()))
    return routes


def collect_openapi_routes(openapi: dict[str, Any]) -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for path, methods in openapi.get("paths", {}).items():
        for method in methods:
            upper_method = method.upper()
            if upper_method in HTTP_METHODS:
                routes.add((upper_method, path))
    return routes


def find_route_doc_issues(
    openapi: dict[str, Any],
    docs_dir: Path,
) -> list[str]:
    code_routes = collect_openapi_routes(openapi)
    code_routes.discard(("GET", "/"))
    documented_routes = collect_documented_routes(docs_dir)

    issues: list[str] = []
    for method, path in sorted(code_routes - documented_routes):
        issues.append(f"代码接口缺少文档: {method} {path}")
    for method, path in sorted(documented_routes - code_routes):
        issues.append(f"文档接口不存在于代码: {method} {path}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 FastAPI OpenAPI 与接口文档是否一致")
    parser.add_argument("--docs-dir", default="planing/接口文档")
    args = parser.parse_args()

    from app.main import app

    issues = find_route_doc_issues(app.openapi(), Path(args.docs_dir))
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("接口文档与 OpenAPI 路径/方法一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
