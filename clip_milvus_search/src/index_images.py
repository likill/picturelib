"""
图片索引脚本
基于 Zilliz 博客: CLIP+Milvus，多模态embedding如何用于以文搜图

功能：
1. 从 zhupicture 数据库读取图片 URL
2. 下载图片并用 CLIP 生成向量
3. 存入 Milvus

支持两种模式：
- db: 从数据库读取图片进行索引
- single: 索引单张图片
"""

import os
import time
import argparse
from glob import glob
from tqdm import tqdm

from src.clip_service import CLIPService, get_clip_service
from src.milvus_service import MilvusService, setup_collection
from config import BATCH_SIZE, IMAGE_EXTENSIONS, DB_CONFIG


def encode_and_insert_images(image_paths, clip_service, milvus_service, batch_size=100):
    """
    批量处理图片并插入 Milvus

    Args:
        image_paths: 图片路径列表
        clip_service: CLIP 服务实例
        milvus_service: Milvus 服务实例
        batch_size: 每批处理数量

    Returns:
        int: 成功处理的数量
    """
    total_images = len(image_paths)
    print(f"总计需要处理 {total_images} 张图片")

    # 初始化总计时器
    total_start_time = time.time()
    success_count = 0

    # 初始化进度条
    with tqdm(total=total_images, desc="处理图片并插入数据") as progress_bar:
        # 分批处理图片
        for batch_start in range(0, total_images, batch_size):
            batch_data = []
            batch_paths = image_paths[batch_start: batch_start + batch_size]
            batch_start_time = time.time()

            # 当前批次的向量化处理
            for image_path in batch_paths:
                try:
                    # 生成图片向量
                    image_embedding = clip_service.encode_image(image_path)

                    batch_data.append({
                        "vectors": image_embedding,
                        "filepath": image_path
                    })
                    success_count += 1

                except Exception as e:
                    print(f"\n处理图片 {image_path} 时出错: {str(e)}")
                    continue

            # 批量插入当前批次到 Milvus
            if batch_data:
                try:
                    milvus_service.insert(data=batch_data)

                    # 计算批次耗时
                    batch_duration = time.time() - batch_start_time

                    # 更新进度条
                    progress_bar.update(len(batch_data))

                    # 显示批次处理时间
                    progress_bar.set_postfix({
                        "批次耗时": f"{batch_duration:.2f}s",
                    })

                except Exception as e:
                    print(f"\n插入批次 {batch_start} 时失败: {str(e)}")

    # 计算总耗时
    total_duration = time.time() - total_start_time
    print(f"\n所有图片处理完成！总耗时: {total_duration:.2f}秒")
    if total_duration > 0:
        print(f"平均处理速度: {success_count / total_duration:.1f}张/秒")

    return success_count


def index_from_local_directory(input_dir_path, ext_list=None, batch_size=300):
    """
    从本地目录索引图片

    Args:
        input_dir_path: 图片目录路径
        ext_list: 支持的文件扩展名列表
        batch_size: 每批处理数量
    """
    if ext_list is None:
        ext_list = IMAGE_EXTENSIONS

    # 1. 初始化服务
    clip_service = CLIPService()
    milvus_service = MilvusService()

    # 2. 设置集合
    setup_collection(milvus_service)

    # 3. 获取所有图片路径
    image_paths = []
    for ext in ext_list:
        image_paths.extend(glob(os.path.join(input_dir_path, f"**/{ext}"), recursive=True))

    print(f"找到 {len(image_paths)} 张图片")

    # 4. 批量处理并插入
    encode_and_insert_images(image_paths, clip_service, milvus_service, batch_size)

    # 5. 验证结果
    count_result = milvus_service.query(output_fields=["count(*)"])
    print(f"集合中现有数据: {count_result}")


def index_from_database(limit=None, batch_size=300):
    """
    从 zhupicture 数据库读取图片进行索引

    Args:
        limit: 限制读取数量，None 表示全部
        batch_size: 每批处理数量
    """
    try:
        import mysql.connector
    except ImportError:
        print("请安装 mysql-connector-python: pip install mysql-connector-python")
        return

    # 1. 连接数据库
    db_config = DB_CONFIG
    print(f"正在连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")

    try:
        conn = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        cursor = conn.cursor()

        # 2. 查询图片 URL
        if limit:
            query = f"SELECT id, url FROM picture WHERE url IS NOT NULL LIMIT {limit}"
        else:
            query = "SELECT id, url FROM picture WHERE url IS NOT NULL"

        cursor.execute(query)
        picture_records = cursor.fetchall()
        print(f"从数据库读取到 {len(picture_records)} 张图片")

        # 3. 初始化服务
        clip_service = CLIPService()
        milvus_service = MilvusService()

        # 4. 设置集合
        setup_collection(milvus_service)

        # 5. 下载并索引每张图片
        success_count = 0
        total_start_time = time.time()

        with tqdm(total=len(picture_records), desc="从数据库索引图片") as progress_bar:
            batch_data = []

            for picture_id, image_url in picture_records:
                try:
                    # 从 URL 下载图片并编码
                    image_embedding = clip_service.encode_image_from_url(image_url)

                    batch_data.append({
                        "vectors": image_embedding,
                        "filepath": image_url
                    })

                    # 达到批次大小时插入
                    if len(batch_data) >= batch_size:
                        milvus_service.insert(data=batch_data)
                        progress_bar.update(len(batch_data))
                        batch_data = []

                    success_count += 1

                except Exception as e:
                    print(f"\n处理图片 {image_url} 时出错: {str(e)}")
                    progress_bar.update(1)
                    continue

            # 插入剩余的数据
            if batch_data:
                milvus_service.insert(data=batch_data)
                progress_bar.update(len(batch_data))

        # 计算总耗时
        total_duration = time.time() - total_start_time
        print(f"\n索引完成！总耗时: {total_duration:.2f}秒")
        print(f"成功处理: {success_count} 张图片")

        # 6. 验证结果
        count_result = milvus_service.query(output_fields=["count(*)"])
        print(f"集合中现有数据: {count_result}")

        # 关闭数据库连接
        cursor.close()
        conn.close()

    except mysql.connector.Error as e:
        print(f"数据库错误: {e}")
    except Exception as e:
        print(f"索引过程中出错: {e}")


def index_single_image(image_url, picture_id=None):
    """
    索引单张图片

    Args:
        image_url: 图片 URL
        picture_id: 可选的图片 ID
    """
    # 1. 初始化服务
    clip_service = CLIPService()
    milvus_service = MilvusService()

    # 2. 检查集合是否存在，如果不存在则创建
    if not milvus_service.milvus_client.has_collection(milvus_service.collection_name):
        print(f"集合 {milvus_service.collection_name} 不存在，正在创建...")
        setup_collection(milvus_service)

    try:
        # 3. 从 URL 下载图片并编码
        print(f"正在处理图片: {image_url}")
        image_embedding = clip_service.encode_image_from_url(image_url)

        # 4. 插入 Milvus
        data = [{
            "vectors": image_embedding,
            "filepath": image_url
        }]

        result = milvus_service.insert(data=data)
        print(f"索引成功！插入结果: {result}")

        return True

    except Exception as e:
        print(f"索引失败: {e}")
        return False


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CLIP + Milvus 图片索引工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 从本地目录索引图片
  python src/index_images.py --mode local --path ./images

  # 从 zhupicture 数据库索引图片（限制 100 张）
  python src/index_images.py --mode db --limit 100

  # 从 zhupicture 数据库索引全部图片
  python src/index_images.py --mode db

  # 索引单张图片
  python src/index_images.py --mode single --url https://example.com/image.jpg
        """
    )

    parser.add_argument(
        "--mode",
        choices=["local", "db", "single"],
        default="local",
        help="索引模式: local(本地目录), db(数据库), single(单张图片)"
    )
    parser.add_argument("--path", help="本地图片目录路径 (mode=local 时使用)")
    parser.add_argument("--limit", type=int, help="从数据库读取的图片数量限制 (mode=db 时使用)")
    parser.add_argument("--url", help="图片 URL (mode=single 时使用)")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help=f"批次大小 (默认: {BATCH_SIZE})")

    args = parser.parse_args()

    if args.mode == "local":
        if not args.path:
            print("错误: --path 参数在 local 模式下是必需的")
            exit(1)
        index_from_local_directory(args.path, batch_size=args.batch_size)

    elif args.mode == "db":
        index_from_database(limit=args.limit, batch_size=args.batch_size)

    elif args.mode == "single":
        if not args.url:
            print("错误: --url 参数在 single 模式下是必需的")
            exit(1)
        index_single_image(args.url)
