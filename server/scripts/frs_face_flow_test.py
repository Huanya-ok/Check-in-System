
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.face_service import face_service


async def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python server/scripts/frs_face_flow_test.py <入库图片> [搜索图片]")
        raise SystemExit(1)

    add_image_path = Path(sys.argv[1])
    search_image_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else add_image_path

    if not add_image_path.exists():
        print(f"入库图片不存在: {add_image_path}")
        raise SystemExit(1)
    if not search_image_path.exists():
        print(f"搜索图片不存在: {search_image_path}")
        raise SystemExit(1)

    external_image_id = f"test-{uuid4().hex[:12]}"
    added = None

    try:
        print(f"添加人脸: {add_image_path} external_image_id={external_image_id}")
        added = await face_service.add_face(external_image_id, add_image_path.read_bytes())
        print("添加结果:", added)

        print("等待云端人脸库索引同步...")
        await asyncio.sleep(5)

        print(f"搜索人脸: {search_image_path}")
        found = await face_service.search(search_image_path.read_bytes())
        print("搜索结果:", found)
    finally:
        if added and added.get("face_id"):
            print(f"删除测试人脸: face_id={added['face_id']}")
            removed = await face_service.remove_face(
                face_id=added["face_id"],
                external_image_id=added.get("external_image_id") or external_image_id,
            )
            print("删除结果:", removed)


if __name__ == "__main__":
    asyncio.run(main())
