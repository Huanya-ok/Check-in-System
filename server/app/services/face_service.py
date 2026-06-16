"""华为云 FRS 人脸识别服务封装。"""

from __future__ import annotations

import asyncio
import base64

from app.config import settings


class FaceRecognitionService:
    def __init__(self) -> None:
        self._client = None
        self._face_set_ready = False

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not settings.huawei_ak or not settings.huawei_sk:
            raise RuntimeError("请配置 HUAWEI_AK 与 HUAWEI_SK 环境变量")

        try:
            from huaweicloudsdkcore.auth.credentials import BasicCredentials
            from huaweicloudsdkfrs.v2.frs_client import FrsClient
            from huaweicloudsdkfrs.v2.region.frs_region import FrsRegion
        except ImportError as exc:
            raise RuntimeError("请安装华为 FRS SDK: pip install huaweicloudsdkcore huaweicloudsdkfrs") from exc

        credentials = BasicCredentials(
            settings.huawei_ak,
            settings.huawei_sk,
            settings.huawei_project_id or None,
        )
        self._client = (
            FrsClient.new_builder()
            .with_credentials(credentials)
            .with_region(FrsRegion.value_of(settings.huawei_frs_region))
            .build()
        )
        return self._client

    def _to_base64(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    def _ensure_face_set(self) -> None:
        if self._face_set_ready:
            return
        from huaweicloudsdkcore.exceptions import exceptions
        from huaweicloudsdkfrs.v2.model.create_face_set_req import CreateFaceSetReq
        from huaweicloudsdkfrs.v2.model.create_face_set_request import CreateFaceSetRequest

        client = self._get_client()
        request = CreateFaceSetRequest()
        request.body = CreateFaceSetReq(
            face_set_name=settings.huawei_face_set_name,
            face_set_capacity=10000,
        )
        try:
            client.create_face_set(request)
        except exceptions.ClientRequestException as exc:
            # 人脸库已存在时继续
            if exc.error_code not in {"FRS.0152", "FRS.0016"} and "already" not in (exc.error_msg or "").lower():
                raise RuntimeError(f"创建华为云人脸库失败: {exc.error_msg}") from exc
        self._face_set_ready = True

    def _detect_face_sync(self, image_bytes: bytes) -> None:
        from huaweicloudsdkfrs.v2.model.face_detect_base64_req import FaceDetectBase64Req
        from huaweicloudsdkfrs.v2.model.detect_face_by_base64_request import DetectFaceByBase64Request

        self._ensure_face_set()
        request = DetectFaceByBase64Request()
        request.body = FaceDetectBase64Req(image_base64=self._to_base64(image_bytes))
        response = self._get_client().detect_face_by_base64(request)
        faces = getattr(response, "faces", None) or []
        if not faces:
            raise ValueError("未检测到人脸")

    def add_face_sync(self, profile_id: int, image_bytes: bytes, existing_frs_face_id: str | None = None) -> str:
        from huaweicloudsdkfrs.v2.model.add_faces_base64_req import AddFacesBase64Req
        from huaweicloudsdkfrs.v2.model.add_faces_by_base64_request import AddFacesByBase64Request

        self._detect_face_sync(image_bytes)
        if existing_frs_face_id:
            self.remove_face_sync(existing_frs_face_id)

        request = AddFacesByBase64Request()
        request.face_set_name = settings.huawei_face_set_name
        request.body = AddFacesBase64Req(
            image_base64=self._to_base64(image_bytes),
            external_image_id=str(profile_id),
        )
        response = self._get_client().add_faces_by_base64(request)
        faces = getattr(response, "faces", None) or []
        if not faces:
            raise ValueError("人脸添加失败，华为云未返回 face_id")
        return str(faces[0].face_id)

    def remove_face_sync(self, frs_face_id: str) -> None:
        if not frs_face_id:
            return
        from huaweicloudsdkcore.exceptions import exceptions
        from huaweicloudsdkfrs.v2.model.delete_face_by_face_id_request import DeleteFaceByFaceIdRequest

        self._ensure_face_set()
        request = DeleteFaceByFaceIdRequest()
        request.face_set_name = settings.huawei_face_set_name
        request.face_id = frs_face_id
        try:
            self._get_client().delete_face_by_face_id(request)
        except exceptions.ClientRequestException:
            return

    def search_sync(self, image_bytes: bytes) -> tuple[int | None, float]:
        from huaweicloudsdkfrs.v2.model.face_search_base64_req import FaceSearchBase64Req
        from huaweicloudsdkfrs.v2.model.search_face_by_base64_request import SearchFaceByBase64Request

        self._ensure_face_set()
        request = SearchFaceByBase64Request()
        request.face_set_name = settings.huawei_face_set_name
        request.body = FaceSearchBase64Req(
            image_base64=self._to_base64(image_bytes),
            top_n=1,
        )
        response = self._get_client().search_face_by_base64(request)
        faces = getattr(response, "faces", None) or []
        if not faces:
            return None, 0.0

        top = faces[0]
        similarity = float(getattr(top, "similarity", 0) or 0)
        if similarity < settings.face_similarity_threshold:
            return None, similarity

        external_id = getattr(top, "external_image_id", None)
        if not external_id:
            return None, similarity
        try:
            return int(external_id), similarity
        except ValueError:
            return None, similarity

    async def detect_face(self, image_bytes: bytes) -> None:
        await asyncio.to_thread(self._detect_face_sync, image_bytes)

    async def add_face(
        self,
        profile_id: int,
        image_bytes: bytes,
        existing_frs_face_id: str | None = None,
    ) -> str:
        return await asyncio.to_thread(self.add_face_sync, profile_id, image_bytes, existing_frs_face_id)

    async def remove_face(self, frs_face_id: str | None) -> None:
        if frs_face_id:
            await asyncio.to_thread(self.remove_face_sync, frs_face_id)

    async def search(self, image_bytes: bytes) -> tuple[int | None, float]:
        return await asyncio.to_thread(self.search_sync, image_bytes)


face_service = FaceRecognitionService()
