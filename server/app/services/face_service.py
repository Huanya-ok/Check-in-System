"""Huawei Cloud FRS face search service.

The service intentionally uses the ByFile APIs so uploaded image bytes can be
forwarded as multipart/form-data without base64 expansion.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class FaceRecognitionService:
    def __init__(self) -> None:
        self._timeout = httpx.Timeout(30.0)

    def _require_config(self) -> None:
        missing = []
        if not settings.huawei_face_endpoint:
            missing.append("HUAWEI_FACE_ENDPOINT")
        if not settings.huawei_project_id:
            missing.append("HUAWEI_PROJECT_ID")
        if not settings.huawei_face_set_name:
            missing.append("HUAWEI_FACE_SET_NAME")
        if not settings.huawei_auth_token:
            missing.append("HUAWEI_AUTH_TOKEN")
        if missing:
            raise RuntimeError(f"缺少华为云 FRS 配置: {', '.join(missing)}")

    def _url(self, suffix: str) -> str:
        self._require_config()
        endpoint = settings.huawei_face_endpoint.rstrip("/")
        project_id = settings.huawei_project_id
        face_set_name = settings.huawei_face_set_name
        return f"{endpoint}/v2/{project_id}/face-sets/{face_set_name}{suffix}"

    def _headers(self) -> dict[str, str]:
        self._require_config()
        return {"X-Auth-Token": settings.huawei_auth_token}

    def _image_file(self, filename: str, image_bytes: bytes) -> dict[str, tuple[str, bytes, str]]:
        if not image_bytes:
            raise ValueError("图片内容为空")
        return {"image_file": (filename, image_bytes, self._guess_content_type(image_bytes))}

    def _guess_content_type(self, image_bytes: bytes) -> str:
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if image_bytes.startswith(b"BM"):
            return "image/bmp"
        return "image/jpeg"

    def _parse_json(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(f"华为云 FRS 返回非 JSON 响应，HTTP {response.status_code}") from exc

        if response.is_error:
            error_code = payload.get("error_code", "unknown")
            error_msg = payload.get("error_msg", response.text)
            if response.status_code in {401, 403}:
                raise RuntimeError(f"华为云 FRS 鉴权失败或 Token 已过期: {error_code} {error_msg}")
            raise RuntimeError(f"华为云 FRS 调用失败: HTTP {response.status_code}, {error_code} {error_msg}")

        return payload

    def _first_face(self, payload: dict[str, Any], empty_message: str) -> dict[str, Any]:
        faces = payload.get("faces") or []
        if not faces:
            raise ValueError(empty_message)
        if not isinstance(faces[0], dict):
            raise RuntimeError("华为云 FRS 返回的人脸结果格式异常")
        return faces[0]

    def _face_result(self, face: dict[str, Any]) -> dict[str, Any]:
        return {
            "face_id": face.get("face_id"),
            "external_image_id": face.get("external_image_id"),
            "bounding_box": face.get("bounding_box"),
        }

    async def add_face(self, external_image_id: str | int, image_bytes: bytes) -> dict[str, Any]:
        """Add one face to the configured FRS face set using AddFacesByFile.

        Args:
            external_image_id: Caller-provided unique person/image identifier.
            image_bytes: Raw uploaded image bytes.

        Returns:
            A dict containing face_id, external_image_id, and bounding_box.
        """
        url = self._url("/faces")
        data = {
            "external_image_id": str(external_image_id),
            "single": "true",
        }
        files = self._image_file("face.jpg", image_bytes)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, headers=self._headers(), data=data, files=files)
        except httpx.RequestError as exc:
            raise RuntimeError(f"无法连接华为云 FRS: {exc.__class__.__name__}") from exc

        payload = self._parse_json(response)
        face = self._first_face(payload, "人脸添加失败，华为云未返回 face_id")
        result = self._face_result(face)
        if not result["face_id"]:
            raise ValueError("人脸添加失败，华为云未返回 face_id")
        return result

    async def search(self, image_bytes: bytes) -> dict[str, Any]:
        """Search the configured FRS face set using SearchFaceByFile.

        Returns:
            A dict containing face_id, external_image_id, similarity, and
            bounding_box for the best match.
        """
        url = self._url("/search")
        data = {
            "top_n": "1",
            "threshold": str(settings.face_similarity_threshold),
        }
        files = self._image_file("checkin.jpg", image_bytes)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, headers=self._headers(), data=data, files=files)
        except httpx.RequestError as exc:
            raise RuntimeError(f"无法连接华为云 FRS: {exc.__class__.__name__}") from exc

        payload = self._parse_json(response)
        face = self._first_face(payload, "未识别到匹配人脸或相似度不足")
        result = self._face_result(face)
        result["similarity"] = float(face.get("similarity") or 0.0)
        if not result["face_id"] and not result["external_image_id"]:
            raise ValueError("人脸搜索成功但缺少 face_id 和 external_image_id")
        return result

    async def remove_face(
        self,
        face_id: str | int | None = None,
        external_image_id: str | int | None = None,
    ) -> dict[str, Any]:
        """Delete a face from the configured FRS face set.

        Prefer face_id. Pass external_image_id when the cloud face_id is not
        available.
        """
        if face_id is None and external_image_id is None:
            raise ValueError("删除人脸需要提供 face_id 或 external_image_id")

        query_key = "face_id" if face_id is not None else "external_image_id"
        query_value = str(face_id if face_id is not None else external_image_id)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.delete(
                    self._url("/faces"),
                    headers=self._headers(),
                    params={query_key: query_value},
                )
        except httpx.RequestError as exc:
            raise RuntimeError(f"无法连接华为云 FRS: {exc.__class__.__name__}") from exc

        payload = self._parse_json(response)
        face_number = int(payload.get("face_number") or 0)
        if face_number <= 0:
            raise ValueError(f"云端未删除任何人脸，{query_key}={query_value} 可能不存在")

        return {
            "face_number": face_number,
            "face_set_id": payload.get("face_set_id"),
            "face_set_name": payload.get("face_set_name"),
            "deleted_by": query_key,
            "deleted_value": query_value,
        }


face_service = FaceRecognitionService()
