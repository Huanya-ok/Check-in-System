"""人脸识别服务：RetinaFace 检测 + ArcFace 编码 + FAISS 检索。"""

from __future__ import annotations

import json
import os
from pathlib import Path

import cv2
import faiss
import numpy as np

from app.config import settings

EMBEDDING_DIM = 512


class FaceRecognitionService:
    def __init__(self) -> None:
        self._app = None
        self._index: faiss.IndexFlatIP | None = None
        self._index_to_profile_id: dict[int, int] = {}
        self._profile_id_to_index: dict[int, int] = {}
        self._next_index = 0

    def _ensure_model(self) -> None:
        if self._app is not None:
            return
        try:
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise RuntimeError("请安装 insightface: pip install insightface onnxruntime") from exc

        self._app = FaceAnalysis(name=settings.face_model_name, providers=["CPUExecutionProvider"])
        self._app.prepare(ctx_id=-1, det_size=(640, 640))
        self._load_index()

    def _load_index(self) -> None:
        index_path = Path(settings.faiss_index_path)
        mapping_path = index_path.with_suffix(".json")
        if index_path.exists() and mapping_path.exists():
            self._index = faiss.read_index(str(index_path))
            data = json.loads(mapping_path.read_text(encoding="utf-8"))
            self._index_to_profile_id = {int(k): v for k, v in data["index_to_profile"].items()}
            self._profile_id_to_index = {int(k): v for k, v in data["profile_to_index"].items()}
            self._next_index = data.get("next_index", len(self._index_to_profile_id))
        else:
            self._index = faiss.IndexFlatIP(EMBEDDING_DIM)

    def _save_index(self) -> None:
        if self._index is None:
            return
        index_path = Path(settings.faiss_index_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(index_path))
        mapping_path = index_path.with_suffix(".json")
        mapping_path.write_text(
            json.dumps(
                {
                    "index_to_profile": self._index_to_profile_id,
                    "profile_to_index": self._profile_id_to_index,
                    "next_index": self._next_index,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _decode_image(self, image_bytes: bytes) -> np.ndarray:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("无法解析图片")
        return img

    def extract_embedding(self, image_bytes: bytes) -> np.ndarray:
        self._ensure_model()
        assert self._app is not None
        img = self._decode_image(image_bytes)
        faces = self._app.get(img)
        if not faces:
            raise ValueError("未检测到人脸")
        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        embedding = face.normed_embedding.astype(np.float32)
        return embedding

    def add_face(self, profile_id: int, image_bytes: bytes) -> int:
        embedding = self.extract_embedding(image_bytes)
        assert self._index is not None

        if profile_id in self._profile_id_to_index:
            idx = self._profile_id_to_index[profile_id]
            self._index.remove_ids(np.array([idx], dtype=np.int64))
            del self._index_to_profile_id[idx]
            del self._profile_id_to_index[profile_id]

        idx = self._next_index
        self._next_index += 1
        self._index.add(embedding.reshape(1, -1))
        self._index_to_profile_id[idx] = profile_id
        self._profile_id_to_index[profile_id] = idx
        self._save_index()
        return idx

    def remove_face(self, profile_id: int) -> None:
        if profile_id not in self._profile_id_to_index:
            return
        idx = self._profile_id_to_index[profile_id]
        assert self._index is not None
        self._index.remove_ids(np.array([idx], dtype=np.int64))
        del self._index_to_profile_id[idx]
        del self._profile_id_to_index[profile_id]
        self._save_index()

    def search(self, image_bytes: bytes) -> tuple[int | None, float]:
        embedding = self.extract_embedding(image_bytes)
        assert self._index is not None
        if self._index.ntotal == 0:
            return None, 0.0

        scores, indices = self._index.search(embedding.reshape(1, -1), 1)
        score = float(scores[0][0])
        idx = int(indices[0][0])
        if idx < 0 or score < settings.face_similarity_threshold:
            return None, score
        profile_id = self._index_to_profile_id.get(idx)
        return profile_id, score


face_service = FaceRecognitionService()
