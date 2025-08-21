from PIL import Image
import os
import glob
from numpy.core.defchararray import upper




def small_size(original_path, i, ii):
    # 创建输出目录
    original_dir = os.path.dirname(original_path)
    output_dir = os.path.join(original_dir, "缩小体积")
    os.makedirs(output_dir, exist_ok=True)  # 自动创建目录

    # 生成输出路径
    file_name = os.path.basename(original_path)
    output_path = os.path.join(output_dir, file_name)


    # 打开原始图片
    with Image.open(original_path) as img:
        original_format = img.format  # 保留原始格式信息
        # 转换格式并保留Alpha通道
        original = img.convert("RGBA")

        try:
            # 构建保存参数
            save_params = img.info.copy()

            # 保存结果（保持原始格式）
            # output_path = f"{os.path.splitext(original_path)[0]}_添加水印{os.path.splitext(original_path)[1]}"
            # 修改保存部分
            original.convert(img.mode).save(
                output_path,
                format=original_format,
                **save_params
            )

            print(f"已处理 {i}/{ii}: {os.path.basename(original_path)}")

        except Exception as e:
            print(f"处理失败：{original_path} - {str(e)}")


if __name__ == "__main__":
    # 支持的图片格式
    extensions = ["jpg", "jpeg", "png", "bmp", "webp"]

    i = 1
    for ext in extensions:
        for file in glob.glob(f"*.{ext}"):
            small_size(file, i, len(glob.glob(f"*.{ext}")))
            i += 1

    print("处理完成！按回车键退出...")
    input()
