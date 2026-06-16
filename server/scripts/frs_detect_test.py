#!/usr/bin/env python3
"""华为云 FRS 本地人脸检测调试脚本。

用法（在 server 目录下）：
  cp .env.example .env   # 填入 HUAWEI_AK / HUAWEI_SK / HUAWEI_PROJECT_ID
  python scripts/frs_detect_test.py path/to/face.jpg
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

# 允许从 server/ 目录直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.services.face_service import face_service


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python scripts/frs_detect_test.py <图片路径>")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"文件不存在: {image_path}")
        sys.exit(1)

    if not settings.huawei_ak or not settings.huawei_sk:
        print("请先在 .env 中配置 HUAWEI_AK、HUAWEI_SK、HUAWEI_PROJECT_ID")
        sys.exit(1)

    image_bytes = image_path.read_bytes()
    print(f"图片大小: {len(image_bytes)} bytes")
    print(f"区域: {settings.huawei_frs_region}")
    print(f"人脸库: {settings.huawei_face_set_name}")
    print("正在调用人脸检测...")

    try:
        face_service._detect_face_sync(image_bytes)
        print("人脸检测成功：图片中包含可识别的人脸")
    except Exception as exc:
        print(f"人脸检测失败: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
