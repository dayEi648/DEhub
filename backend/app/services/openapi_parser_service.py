"""OpenAPI 文档解析服务：拆分为端点分片并生成可嵌入文本。"""

from __future__ import annotations

import hashlib
import json

from app.core.config import settings


class OpenAPIParserService:
    """OpenAPI 文档解析服务。"""

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def parse(
        self,
        content: bytes,
        filename: str,
        document_id: int,
    ) -> list[dict]:
        """解析文档内容并生成端点分片列表。"""
        spec = self._load_spec(content, filename)
        schemas = self._extract_schemas(spec)
        return self._build_chunks(spec, document_id, schemas)

    # ------------------------------------------------------------------
    # 私有工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _load_spec(content: bytes, filename: str) -> dict:
        """根据扩展名加载 JSON 或 YAML。"""
        text = content.decode("utf-8")
        lower_name = filename.lower()

        if lower_name.endswith(".json"):
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON 解析失败: {exc}") from exc

        if lower_name.endswith(".yaml") or lower_name.endswith(".yml"):
            try:
                import yaml
                return yaml.safe_load(text) or {}
            except Exception as exc:
                raise ValueError(f"YAML 解析失败: {exc}") from exc

        raise ValueError(f"不支持的文件格式: {filename}，仅支持 .json / .yaml / .yml")

    @staticmethod
    def _extract_schemas(spec: dict) -> dict:
        """提取全局 Schema 定义（支持 OpenAPI 3.x 和 Swagger 2.0）。"""
        # OpenAPI 3.x
        schemas = spec.get("components", {}).get("schemas", {})
        if schemas:
            return schemas
        # Swagger 2.0
        return spec.get("definitions", {})

    def _build_chunks(
        self,
        spec: dict,
        document_id: int,
        schemas: dict,
    ) -> list[dict]:
        """按 path + method 构建端点分片。"""
        paths = spec.get("paths", {})
        if not paths:
            return []

        chunks: list[dict] = []
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            path_level_parameters = methods.get("parameters", [])
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue
                # 跳过 OpenAPI 的 parameters / $ref 等非操作字段
                if method.startswith("x-") or method == "parameters":
                    continue
                merged_operation = dict(operation)
                merged_parameters: list[dict] = []
                if isinstance(path_level_parameters, list):
                    merged_parameters.extend(
                        [p for p in path_level_parameters if isinstance(p, dict)]
                    )
                op_parameters = operation.get("parameters", [])
                if isinstance(op_parameters, list):
                    merged_parameters.extend(
                        [p for p in op_parameters if isinstance(p, dict)]
                    )
                if merged_parameters:
                    merged_operation["parameters"] = merged_parameters
                chunk = self._build_chunk(
                    path=path,
                    method=method,
                    operation=merged_operation,
                    schemas=schemas,
                    document_id=document_id,
                    index=len(chunks),
                )
                chunks.append(chunk)
        return chunks

    def _build_chunk(
        self,
        path: str,
        method: str,
        operation: dict,
        schemas: dict,
        document_id: int,
        index: int,
    ) -> dict:
        """构建单个端点分片字典。"""
        path_clean = (
            path.replace("/", "_")
            .replace("{", "")
            .replace("}", "")
            .replace("-", "_")
        )
        chunk_id = f"ep_{index}_{method.upper()}_{path_clean}_{document_id}"
        content = self._build_chunk_text(path, method, operation, schemas)
        content_hash = self._compute_content_hash(content)

        tags = operation.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        return {
            "chunk_id": chunk_id,
            "path": path,
            "method": method.upper(),
            "summary": operation.get("summary", ""),
            "description": operation.get("description", ""),
            "tags": tags,
            "operation_id": operation.get("operationId", ""),
            "content": content,
            "content_hash": content_hash,
        }

    def _build_chunk_text(
        self,
        path: str,
        method: str,
        operation: dict,
        schemas: dict,
    ) -> str:
        """构建单个端点的可读文本描述。"""
        lines = [f"API Endpoint: {method.upper()} {path}"]

        if operation.get("summary"):
            lines.append(f"Summary: {operation['summary']}")
        if operation.get("description"):
            lines.append(f"Description: {operation['description']}")

        # 参数提取（含 required / enum / default 约束）
        for param in operation.get("parameters", []):
            if isinstance(param, dict):
                if param.get("in") == "body" and isinstance(param.get("schema"), dict):
                    lines.append("Request Body (application/json):")
                    req_required = set(param["schema"].get("required", []))
                    lines.extend(
                        self._describe_schema(
                            param["schema"], schemas, indent=2, required_set=req_required
                        )
                    )
                    continue
                param_schema = param.get("schema", {})
                param_type = param_schema.get("type", "unknown")
                constraints = self._extract_constraints(param_schema)
                req_mark = " [必填]" if param.get("required") else ""
                lines.append(
                    f"  - {param.get('name', '')}{req_mark} ({param.get('in', '')}, "
                    f"{param_type}): {param.get('description', '')}{constraints}"
                )

        request_body = operation.get("requestBody", {})
        if request_body:
            for media_type, media_obj in request_body.get("content", {}).items():
                lines.append(f"Request Body ({media_type}):")
                req_schema = media_obj.get("schema", {})
                req_required = set(req_schema.get("required", []))
                lines.extend(
                    self._describe_schema(
                        req_schema, schemas, indent=2, required_set=req_required
                    )
                )

        # 响应提取：优先 200/201，再提取常见错误响应
        resp_statuses = ["200", "201", "400", "401", "403", "404", "500"]
        for status in resp_statuses:
            if status in operation.get("responses", {}):
                resp = operation["responses"][status]
                lines.append(f"Response {status}: {resp.get('description', '')}")
                for media_type, media_obj in resp.get("content", {}).items():
                    lines.append(f"  Response Body ({media_type}):")
                    resp_schema = media_obj.get("schema", {})
                    resp_required = set(resp_schema.get("required", []))
                    lines.extend(
                        self._describe_schema(
                            resp_schema, schemas, indent=4, required_set=resp_required
                        )
                    )

        return "\n".join(lines)

    @staticmethod
    def _extract_constraints(prop_schema: dict) -> str:
        """提取并格式化 Schema 约束（enum / default / format）。"""
        parts: list[str] = []
        if "enum" in prop_schema:
            parts.append(f"enum={prop_schema['enum']}")
        if "default" in prop_schema:
            parts.append(f"default={prop_schema['default']}")
        if "format" in prop_schema:
            parts.append(f"format={prop_schema['format']}")
        if parts:
            return f" [{', '.join(parts)}]"
        return ""

    def _describe_schema(
        self,
        schema: dict,
        schemas: dict,
        indent: int = 0,
        required_set: set[str] | None = None,
    ) -> list[str]:
        """递归描述 Schema 结构（支持 $ref、allOf、oneOf、anyOf）。"""
        lines: list[str] = []
        prefix = "  " * indent
        required_set = required_set or set()

        if not isinstance(schema, dict):
            return lines

        ref = schema.get("$ref")
        if ref and isinstance(ref, str):
            ref_name = ref.split("/")[-1]
            if ref_name in schemas:
                ref_schema = schemas[ref_name]
                ref_required = set(ref_schema.get("required", []))
                lines.extend(
                    self._describe_schema(
                        ref_schema,
                        schemas,
                        indent,
                        required_set=required_set | ref_required,
                    )
                )
            else:
                lines.append(f"{prefix}Reference: {ref_name}")
            return lines

        # 处理组合 schema
        for combo_key in ("allOf", "oneOf", "anyOf"):
            if combo_key in schema:
                lines.append(f"{prefix}{combo_key}:")
                for idx, sub_schema in enumerate(schema[combo_key]):
                    if isinstance(sub_schema, dict):
                        lines.append(f"{prefix}  [{idx}]:")
                        lines.extend(
                            self._describe_schema(
                                sub_schema, schemas, indent + 2, required_set=required_set
                            )
                        )
                return lines

        schema_type = schema.get("type", "object")
        if schema_type == "object":
            for prop_name, prop_schema in schema.get("properties", {}).items():
                if not isinstance(prop_schema, dict):
                    continue
                prop_type = prop_schema.get("type", "unknown")
                req_mark = " [必填]" if prop_name in required_set else ""
                constraints = self._extract_constraints(prop_schema)
                lines.append(
                    f"{prefix}- {prop_name}{req_mark} ({prop_type}): "
                    f"{prop_schema.get('description', '')}{constraints}"
                )
                if prop_type == "object" or "$ref" in prop_schema or "allOf" in prop_schema:
                    sub_required = set(prop_schema.get("required", []))
                    lines.extend(
                        self._describe_schema(
                            prop_schema, schemas, indent + 2, required_set=sub_required
                        )
                    )
        elif schema_type == "array":
            lines.append(f"{prefix}Array items:")
            item_schema = schema.get("items", {})
            item_required = set(item_schema.get("required", []))
            lines.extend(
                self._describe_schema(
                    item_schema, schemas, indent + 2, required_set=item_required
                )
            )
        else:
            constraints = self._extract_constraints(schema)
            lines.append(f"{prefix}Type: {schema_type}{constraints}")

        return lines

    @staticmethod
    def _compute_content_hash(text: str) -> str:
        """计算文本的 MD5 指纹（32 位十六进制字符串）。"""
        return hashlib.md5(text.encode("utf-8")).hexdigest()
