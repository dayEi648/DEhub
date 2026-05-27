"""OpenAPIParserService 单元测试（阶段 2）。"""

import pytest

from app.services.openapi_parser_service import OpenAPIParserService


class TestOpenAPIParserService:
    """测试 OpenAPI 文档解析服务。"""

    @pytest.fixture
    def service(self):
        return OpenAPIParserService()

    # ------------------------------------------------------------------
    # JSON / YAML 基础解析
    # ------------------------------------------------------------------

    def test_parse_json_openapi(self, service):
        """JSON 格式的 OpenAPI 3.x 文档应正确解析出端点。"""
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户列表",
                        "description": "分页获取所有用户",
                        "operationId": "listUsers",
                        "tags": ["user"],
                        "parameters": [
                            {"name": "page", "in": "query", "schema": {"type": "integer"}, "description": "页码"}
                        ],
                        "responses": {"200": {"description": "用户列表"}},
                    },
                    "post": {
                        "summary": "创建用户",
                        "operationId": "createUser",
                        "tags": ["user"],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
                                }
                            }
                        },
                        "responses": {"201": {"description": "创建成功"}},
                    },
                }
            },
        }
        import json
        content = json.dumps(spec).encode("utf-8")
        chunks = service.parse(content, "api.json", document_id=1)

        assert len(chunks) == 2
        assert chunks[0]["path"] == "/users"
        assert chunks[0]["method"] == "GET"
        assert chunks[0]["summary"] == "获取用户列表"
        assert "分页获取所有用户" in chunks[0]["content"]
        assert "page" in chunks[0]["content"]
        assert chunks[0]["operation_id"] == "listUsers"
        assert chunks[0]["tags"] == ["user"]

        assert chunks[1]["method"] == "POST"
        assert "创建用户" in chunks[1]["content"]
        assert chunks[1]["operation_id"] == "createUser"

    def test_parse_yaml_openapi(self, service):
        """YAML 格式的 OpenAPI 3.x 文档应正确解析出端点。"""
        yaml_content = """
openapi: "3.0.0"
paths:
  /posts:
    get:
      summary: "获取文章列表"
      operationId: "listPosts"
      tags: ["blog"]
      responses:
        "200":
          description: "文章列表"
""".encode("utf-8")
        chunks = service.parse(yaml_content, "api.yaml", document_id=2)

        assert len(chunks) == 1
        assert chunks[0]["path"] == "/posts"
        assert chunks[0]["method"] == "GET"
        assert chunks[0]["summary"] == "获取文章列表"
        assert chunks[0]["operation_id"] == "listPosts"
        assert chunks[0]["tags"] == ["blog"]

    def test_parse_empty_paths_returns_empty(self, service):
        """空 paths 应返回零端点。"""
        import json
        spec = {"openapi": "3.0.0", "paths": {}}
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=3)
        assert chunks == []

    def test_parse_missing_paths_returns_empty(self, service):
        """没有 paths 字段应返回零端点。"""
        import json
        spec = {"openapi": "3.0.0"}
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=4)
        assert chunks == []

    def test_parse_invalid_json_raises(self, service):
        """非法 JSON 应返回明确错误。"""
        with pytest.raises(ValueError, match="JSON"):
            service.parse(b"not json", "api.json", document_id=5)

    def test_parse_invalid_yaml_raises(self, service):
        """非法 YAML 应返回明确错误。"""
        with pytest.raises(ValueError, match="YAML"):
            service.parse(b"\t\t\t{broken", "api.yaml", document_id=6)

    def test_parse_unsupported_extension_raises(self, service):
        """不支持的文件扩展名应返回明确错误。"""
        with pytest.raises(ValueError, match="格式"):
            service.parse(b"{}", "api.txt", document_id=7)

    # ------------------------------------------------------------------
    # Swagger 2.0 兼容
    # ------------------------------------------------------------------

    def test_parse_swagger_2_basic(self, service):
        """Swagger 2.0 基础 paths 结构应可解析。"""
        import json
        spec = {
            "swagger": "2.0",
            "paths": {
                "/items": {
                    "get": {
                        "summary": "获取项目列表",
                        "operationId": "listItems",
                    }
                }
            },
        }
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=8)
        assert len(chunks) == 1
        assert chunks[0]["path"] == "/items"
        assert chunks[0]["summary"] == "获取项目列表"

    def test_parse_path_level_parameters_should_merge_into_operation(self, service):
        """path 级 parameters 应并入 operation 结果。"""
        import json

        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users/{id}": {
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "用户ID",
                        }
                    ],
                    "get": {
                        "summary": "查询用户",
                        "responses": {"200": {"description": "OK"}},
                    },
                }
            },
        }
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=81)
        assert len(chunks) == 1
        assert "id [必填] (path, string): 用户ID" in chunks[0]["content"]

    def test_parse_swagger2_body_parameter_should_be_rendered(self, service):
        """Swagger 2.0 的 in=body 参数应被展开进请求体描述。"""
        import json

        spec = {
            "swagger": "2.0",
            "paths": {
                "/login": {
                    "post": {
                        "summary": "登录",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {
                                            "type": "string",
                                            "description": "用户名",
                                        },
                                        "password": {
                                            "type": "string",
                                            "description": "密码",
                                        },
                                    },
                                },
                            }
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
        }
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=82)
        assert len(chunks) == 1
        assert "Request Body (application/json):" in chunks[0]["content"]
        assert "username (string): 用户名" in chunks[0]["content"]
        assert "password (string): 密码" in chunks[0]["content"]

    # ------------------------------------------------------------------
    # $ref 展开
    # ------------------------------------------------------------------

    def test_parse_ref_object_expansion(self, service):
        """基础 $ref object 应能展开。"""
        import json
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "post": {
                        "summary": "创建用户",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "responses": {"201": {"description": "创建成功"}},
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "用户名"},
                            "age": {"type": "integer", "description": "年龄"},
                        }
                    }
                }
            },
        }
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=9)
        content = chunks[0]["content"]
        assert "name (string): 用户名" in content
        assert "age (integer): 年龄" in content

    def test_parse_ref_request_body_keeps_component_required_fields(self, service):
        """requestBody 直接 $ref 到组件 schema 时，应保留组件内 required 标记。"""
        import json

        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "post": {
                        "summary": "创建用户",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UserCreate"}
                                }
                            }
                        },
                        "responses": {"201": {"description": "创建成功"}},
                    }
                }
            },
            "components": {
                "schemas": {
                    "UserCreate": {
                        "type": "object",
                        "required": ["username", "password"],
                        "properties": {
                            "username": {"type": "string", "description": "用户名"},
                            "password": {"type": "string", "description": "密码"},
                            "nickname": {"type": "string", "description": "昵称"},
                        },
                    }
                }
            },
        }
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=16)
        content = chunks[0]["content"]

        assert "username [必填] (string): 用户名" in content
        assert "password [必填] (string): 密码" in content
        assert "nickname (string): 昵称" in content

    def test_parse_ref_array_expansion(self, service):
        """基础 $ref array 应能展开。"""
        import json
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户列表",
                        "responses": {
                            "200": {
                                "description": "用户列表",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "用户名"},
                        }
                    }
                }
            },
        }
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=10)
        content = chunks[0]["content"]
        assert "Array items:" in content
        assert "name (string): 用户名" in content

    def test_parse_unresolved_ref_keeps_name(self, service):
        """无法解析的 $ref 应保留引用名称，不报错。"""
        import json
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户",
                        "responses": {
                            "200": {
                                "description": "用户",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Unknown"}
                                    }
                                }
                            }
                        },
                    }
                }
            },
        }
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=11)
        content = chunks[0]["content"]
        assert "Unknown" in content

    def test_parse_success_and_error_responses_together(self, service):
        """存在成功响应时，也应保留常见错误响应，供 RAG 回答异常语义。"""
        import json

        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/login": {
                    "post": {
                        "summary": "用户登录",
                        "responses": {
                            "200": {
                                "description": "登录成功",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "access_token": {
                                                    "type": "string",
                                                    "description": "访问令牌",
                                                }
                                            },
                                        }
                                    }
                                },
                            },
                            "400": {
                                "description": "请求参数错误",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {
                                                    "type": "string",
                                                    "description": "错误信息",
                                                }
                                            },
                                        }
                                    }
                                },
                            },
                        },
                    }
                }
            },
        }
        chunks = service.parse(json.dumps(spec).encode(), "api.json", document_id=17)
        content = chunks[0]["content"]

        assert "Response 200: 登录成功" in content
        assert "access_token (string): 访问令牌" in content
        assert "Response 400: 请求参数错误" in content
        assert "message (string): 错误信息" in content

    # ------------------------------------------------------------------
    # content_hash 生成
    # ------------------------------------------------------------------

    def test_content_hash_consistency(self, service):
        """相同内容应生成相同 content_hash。"""
        import json
        spec = {"openapi": "3.0.0", "paths": {"/ping": {"get": {"summary": "健康检查"}}}}
        content = json.dumps(spec).encode()
        chunks1 = service.parse(content, "api.json", document_id=12)
        chunks2 = service.parse(content, "api.json", document_id=13)
        assert chunks1[0]["content_hash"] == chunks2[0]["content_hash"]

    def test_content_hash_uniqueness(self, service):
        """不同内容应生成不同 content_hash。"""
        import json
        spec1 = {"openapi": "3.0.0", "paths": {"/a": {"get": {"summary": "A"}}}}
        spec2 = {"openapi": "3.0.0", "paths": {"/b": {"get": {"summary": "B"}}}}
        chunks1 = service.parse(json.dumps(spec1).encode(), "api.json", document_id=14)
        chunks2 = service.parse(json.dumps(spec2).encode(), "api.json", document_id=15)
        assert chunks1[0]["content_hash"] != chunks2[0]["content_hash"]
