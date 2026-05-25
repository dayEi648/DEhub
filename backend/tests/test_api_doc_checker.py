from pathlib import Path

from scripts.check_api_docs import collect_documented_routes, find_route_doc_issues


def test_collect_documented_routes_reads_method_and_path(tmp_path: Path):
    docs_dir = tmp_path / "接口文档"
    docs_dir.mkdir()
    (docs_dir / "用户接口文档.md").write_text(
        "#### GET /api/v1/users/{user_id}\n\n获取用户\n",
        encoding="utf-8",
    )

    documented = collect_documented_routes(docs_dir)

    assert ("GET", "/api/v1/users/{user_id}") in documented


def test_find_route_doc_issues_reports_missing_code_routes(tmp_path: Path):
    docs_dir = tmp_path / "接口文档"
    docs_dir.mkdir()
    (docs_dir / "用户接口文档.md").write_text(
        "#### GET /api/v1/users/{user_id}\n",
        encoding="utf-8",
    )
    openapi = {
        "paths": {
            "/api/v1/users/{user_id}": {"get": {}},
            "/api/v1/blog-posts/": {"post": {}},
        }
    }

    issues = find_route_doc_issues(openapi, docs_dir)

    assert "代码接口缺少文档: POST /api/v1/blog-posts/" in issues
