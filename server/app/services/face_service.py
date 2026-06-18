"""Huawei Cloud FRS face search service using the official Python SDK."""

from __future__ import annotations

import asyncio
import base64
import time
from typing import Any

from app.config import settings


class FaceRecognitionService:
    def __init__(self) -> None:
        self._client = None

    def _ak(self) -> str:
        return settings.huaweicloud_sdk_ak or settings.huawei_ak

    def _sk(self) -> str:
        return settings.huaweicloud_sdk_sk or settings.huawei_sk

    def _region(self) -> str:
        return settings.huawei_region or settings.huawei_frs_region

    def _require_config(self) -> None:
        missing = []
        if not self._ak():
            missing.append("HUAWEICLOUD_SDK_AK")
        if not self._sk():
            missing.append("HUAWEICLOUD_SDK_SK")
        if not settings.huawei_project_id:
            missing.append("HUAWEI_PROJECT_ID")
        if not self._region():
            missing.append("HUAWEI_REGION")
        if not settings.huawei_face_set_name:
            missing.append("HUAWEI_FACE_SET_NAME")
        if missing:
            raise RuntimeError(f"缺少华为云 FRS SDK 配置: {', '.join(missing)}")

    def _get_client(self):
        if self._client is not None:
            return self._client

        self._require_config()
        try:
            from huaweicloudsdkcore.auth.credentials import BasicCredentials
            from huaweicloudsdkfrs.v2 import FrsClient
            from huaweicloudsdkfrs.v2.region.frs_region import FrsRegion
        except ImportError as exc:
            raise RuntimeError("请安装华为云 FRS SDK: pip install huaweicloudsdkcore huaweicloudsdkfrs") from exc

        credentials = BasicCredentials(self._ak(), self._sk(), settings.huawei_project_id)
        self._client = (
            FrsClient.new_builder(FrsClient)
            .with_credentials(credentials)
            .with_region(FrsRegion.value_of(self._region()))
            .build()
        )
        return self._client

    def _to_base64(self, image_bytes: bytes) -> str:
        if not image_bytes:
            raise ValueError("图片内容为空")
        return base64.b64encode(image_bytes).decode("utf-8")

    def _to_dict(self, obj: Any) -> dict[str, Any]:
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return {
            "face_id": getattr(obj, "face_id", None),
            "external_image_id": getattr(obj, "external_image_id", None),
            "similarity": getattr(obj, "similarity", None),
            "bounding_box": getattr(obj, "bounding_box", None),
        }

    def _first_face(self, response: Any, empty_message: str) -> dict[str, Any]:
        response_dict = self._to_dict(response)
        faces = response_dict.get("faces") or []
        if not faces:
            raise ValueError(empty_message)
        return self._to_dict(faces[0])

    def _face_result(self, face: dict[str, Any]) -> dict[str, Any]:
        return {
            "face_id": face.get("face_id"),
            "external_image_id": face.get("external_image_id"),
            "bounding_box": face.get("bounding_box"),
        }

    def _sdk_error(self, action: str, exc: Exception) -> RuntimeError:
        try:
            from huaweicloudsdkcore.exceptions import exceptions
        except ImportError:
            exceptions = None

        if exceptions and isinstance(exc, exceptions.ClientRequestException):
            error_code = getattr(exc, "error_code", "unknown")
            error_msg = getattr(exc, "error_msg", str(exc))
            return RuntimeError(f"华为云 FRS {action}失败: {error_code} {error_msg}")
        return RuntimeError(f"华为云 FRS {action}失败: {exc.__class__.__name__}")

    def _is_missing_delete_target(self, exc: Exception) -> bool:
        try:
            from huaweicloudsdkcore.exceptions import exceptions
        except ImportError:
            return False

        return isinstance(exc, exceptions.ClientRequestException) and getattr(exc, "error_code", None) == "FRS.0401"

    def _delete_by_face_id(self, face_id: str | int):
        from huaweicloudsdkfrs.v2 import DeleteFaceByFaceIdRequest

        request = DeleteFaceByFaceIdRequest()
        request.face_set_name = settings.huawei_face_set_name
        request.face_id = str(face_id)
        return self._get_client().delete_face_by_face_id(request)

    def _delete_by_external_image_id(self, external_image_id: str | int):
        from huaweicloudsdkfrs.v2 import DeleteFaceByExternalImageIdRequest

        request = DeleteFaceByExternalImageIdRequest()
        request.face_set_name = settings.huawei_face_set_name
        request.external_image_id = str(external_image_id)
        return self._get_client().delete_face_by_external_image_id(request)

    def _add_face_sync(self, external_image_id: str | int, image_bytes: bytes) -> dict[str, Any]:
        from huaweicloudsdkfrs.v2 import AddFacesBase64Req, AddFacesByBase64Request

        request = AddFacesByBase64Request()
        request.face_set_name = settings.huawei_face_set_name
        request.body = AddFacesBase64Req(
            image_base64=self._to_base64(image_bytes),
            external_image_id=str(external_image_id),
            single=True,
        )

        try:
            response = self._get_client().add_faces_by_base64(request)
        except Exception as exc:
            raise self._sdk_error("添加人脸", exc) from exc

        face = self._first_face(response, "人脸添加失败，华为云未返回 face_id")
        result = self._face_result(face)
        if not result["face_id"]:
            raise ValueError("人脸添加失败，华为云未返回 face_id")
        return result

    def _search_sync(self, image_bytes: bytes) -> dict[str, Any]:
        from huaweicloudsdkfrs.v2 import FaceSearchBase64Req, SearchFaceByBase64Request

        request = SearchFaceByBase64Request()
        request.face_set_name = settings.huawei_face_set_name
        request.body = FaceSearchBase64Req(
            image_base64=self._to_base64(image_bytes),
            top_n=1,
            threshold=settings.face_similarity_threshold,
        )

        try:
            response = self._get_client().search_face_by_base64(request)
        except Exception as exc:
            raise self._sdk_error("搜索人脸", exc) from exc

        face = self._first_face(response, "未识别到匹配人脸或相似度不足")
        result = self._face_result(face)
        result["similarity"] = float(face.get("similarity") or 0.0)
        if not result["face_id"] and not result["external_image_id"]:
            raise ValueError("人脸搜索成功但缺少 face_id 和 external_image_id")
        return result

    def _remove_face_sync(
        self,
        face_id: str | int | None = None,
        external_image_id: str | int | None = None,
    ) -> dict[str, Any]:
        if face_id is None and external_image_id is None:
            raise ValueError("删除人脸需要提供 face_id 或 external_image_id")

        attempts = 4
        delay_seconds = 2
        last_error: Exception | None = None
        for attempt in range(attempts):
            if attempt:
                time.sleep(delay_seconds)

            if face_id is not None:
                deleted_by = "face_id"
                deleted_value = str(face_id)
                try:
                    response = self._delete_by_face_id(face_id)
                    break
                except Exception as exc:
                    last_error = exc
                    if not self._is_missing_delete_target(exc) or external_image_id is None:
                        raise self._sdk_error("删除人脸", exc) from exc

            if external_image_id is not None:
                deleted_by = "external_image_id"
                deleted_value = str(external_image_id)
                try:
                    response = self._delete_by_external_image_id(external_image_id)
                    break
                except Exception as exc:
                    last_error = exc
                    if not self._is_missing_delete_target(exc):
                        raise self._sdk_error("删除人脸", exc) from exc
        else:
            assert last_error is not None
            raise self._sdk_error("删除人脸", last_error) from last_error

        response_dict = self._to_dict(response)
        face_number = int(response_dict.get("face_number") or 0)
        if face_number <= 0:
            raise ValueError(f"云端未删除任何人脸，{deleted_by}={deleted_value} 可能不存在")

        return {
            "face_number": face_number,
            "face_set_id": response_dict.get("face_set_id"),
            "face_set_name": response_dict.get("face_set_name"),
            "deleted_by": deleted_by,
            "deleted_value": deleted_value,
        }

    async def add_face(self, external_image_id: str | int, image_bytes: bytes) -> dict[str, Any]:
        """Add one face to the configured FRS face set using AddFacesByBase64."""
        return await asyncio.to_thread(self._add_face_sync, external_image_id, image_bytes)

    async def search(self, image_bytes: bytes) -> dict[str, Any]:
        """Search the configured FRS face set using SearchFaceByBase64."""
        return await asyncio.to_thread(self._search_sync, image_bytes)

    async def remove_face(
        self,
        face_id: str | int | None = None,
        external_image_id: str | int | None = None,
    ) -> dict[str, Any]:
        """Delete a face by face_id first, or external_image_id as fallback."""
        return await asyncio.to_thread(self._remove_face_sync, face_id, external_image_id)


face_service = FaceRecognitionService()
