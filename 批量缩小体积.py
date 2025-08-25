from PIL import Image
import os
import glob
import concurrent.futures
import threading
from tqdm import tqdm
import time

# 创建线程锁以确保进度更新安全
progress_lock = threading.Lock()


def small_size(original_path, pbar):
    try:
        # 打开原始图片
        with Image.open(original_path) as img:
            original_format = img.format  # 保留原始格式信息
            # 转换格式并保留Alpha通道
            original = img.convert("RGBA")

            # 构建保存参数
            save_params = img.info.copy()

            # 保存结果（直接覆盖原文件）
            original.convert(img.mode).save(
                original_path,  # 直接使用原路径覆盖
                format=original_format,
                **save_params
            )

            # 更新进度条描述
            pbar.set_description(f"处理: {os.path.basename(original_path)[:20]}...")

        return True, original_path
    except Exception as e:
        return False, f"{original_path} - {str(e)}"


if __name__ == "__main__":
    # 支持的图片格式
    extensions = ["jpg", "jpeg", "png", "bmp", "webp"]

    # 获取所有文件（包括子文件夹）
    all_files = []
    for ext in extensions:
        # 使用递归搜索所有子文件夹中的图片
        all_files.extend(glob.glob(f"**/*.{ext}", recursive=True))
        # 添加大写扩展名
        all_files.extend(glob.glob(f"**/*.{ext.upper()}", recursive=True))

    # 移除可能的重复项
    all_files = list(set(all_files))

    if not all_files:
        print("未找到任何图片文件！")
        print("按回车键退出...")
        input()
        exit()

    print(f"找到 {len(all_files)} 个图片文件，开始处理...")

    # 创建进度条
    pbar = tqdm(total=len(all_files), unit="文件", desc="准备处理")

    # 使用线程池并行处理
    successful = 0
    failed_files = []

    # 使用线程池处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        # 提交所有任务
        futures = {executor.submit(small_size, file, pbar): file for file in all_files}

        # 处理完成的任务
        for future in concurrent.futures.as_completed(futures):
            file = futures[future]
            try:
                success, result = future.result()
                if success:
                    successful += 1
                else:
                    failed_files.append(result)
            except Exception as e:
                failed_files.append(f"{file} - {str(e)}")

            # 更新进度条
            pbar.update(1)

    # 关闭进度条
    pbar.close()

    # 输出处理结果
    print(f"\n处理完成！成功: {successful}, 失败: {len(failed_files)}")

    if failed_files:
        print("\n失败的文件列表:")
        for i, file in enumerate(failed_files, 1):
            print(f"{i}. {file}")

    print("\n按回车键退出...")
    input()