"""
CLIP + Milvus 多模态以文搜图服务启动入口
基于 Zilliz 博客: CLIP+Milvus，多模态embedding如何用于以文搜图

使用方法:
    python src/main.py                  # 启动 API 服务
    python src/main.py --setup          # 初始化并设置集合
    python src/main.py --index-db        # 从数据库索引图片
    python src/main.py --index-local     # 从本地目录索引图片
"""

import argparse
import uvicorn

from src.clip_service import CLIPService
from src.milvus_service import MilvusService, setup_collection
from config import API_HOST, API_PORT


def start_api_server(host=None, port=None):
    """
    启动 FastAPI 服务

    Args:
        host: 监听地址
        port: 监听端口
    """
    host = host or API_HOST
    port = port or API_PORT

    print("=" * 50)
    print("CLIP + Milvus 多模态以文搜图服务")
    print("=" * 50)
    print(f"API 服务地址: http://{host}:{port}")
    print(f"API 文档: http://{host}:{port}/docs")
    print("=" * 50)

    uvicorn.run(
        "src.search_api:app",
        host=host,
        port=port,
        reload=True
    )


def setup_milvus_collection():
    """
    初始化并设置 Milvus 集合
    """
    print("正在初始化 CLIP 服务...")
    clip_service = CLIPService()

    print("\n正在初始化 Milvus 服务...")
    milvus_service = MilvusService()

    print("\n正在设置集合...")
    setup_collection(milvus_service)

    print("\n验证集合状态...")
    state = milvus_service.get_load_state()
    print(f"集合加载状态: {state}")

    count_result = milvus_service.query(output_fields=["count(*)"])
    print(f"集合中数据数量: {count_result}")

    print("\n集合设置完成！")


def index_from_local(path):
    """
    从本地目录索引图片

    Args:
        path: 图片目录路径
    """
    from src.index_images import index_from_local_directory
    index_from_local_directory(path)


def index_from_db(limit=None):
    """
    从数据库索引图片

    Args:
        limit: 限制数量
    """
    from src.index_images import index_from_database
    index_from_database(limit=limit)


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CLIP + Milvus 多模态以文搜图服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 启动 API 服务
  python src/main.py

  # 启动服务并指定端口
  python src/main.py --port 8080

  # 初始化并设置 Milvus 集合
  python src/main.py --setup

  # 从本地目录索引图片
  python src/main.py --index-local --path ./images

  # 从 zhupicture 数据库索引图片
  python src/main.py --index-db
  python src/main.py --index-db --limit 100
        """
    )

    parser.add_argument("--host", default=API_HOST, help=f"API 服务地址 (默认: {API_HOST})")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"API 服务端口 (默认: {API_PORT})")
    parser.add_argument("--setup", action="store_true", help="初始化并设置 Milvus 集合")
    parser.add_argument("--index-local", action="store_true", help="从本地目录索引图片")
    parser.add_argument("--index-db", action="store_true", help="从 zhupicture 数据库索引图片")
    parser.add_argument("--path", help="本地图片目录路径 (--index-local 时使用)")
    parser.add_argument("--limit", type=int, help="从数据库读取的图片数量限制")

    args = parser.parse_args()

    # 根据参数执行不同操作
    if args.setup:
        setup_milvus_collection()

    elif args.index_local:
        if not args.path:
            print("错误: --path 参数在 --index-local 模式下是必需的")
            exit(1)
        index_from_local(args.path)

    elif args.index_db:
        index_from_db(limit=args.limit)

    else:
        # 默认启动 API 服务
        start_api_server(host=args.host, port=args.port)
