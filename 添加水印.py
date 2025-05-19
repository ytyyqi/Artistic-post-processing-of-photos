from PIL import Image
import os
import glob


# from rich.progress import Progress


def calculate_brightness(img):
    """计算图片区域的平均亮度"""
    pixels = img.convert("L").getdata()
    return sum(pixels) / len(pixels)


def add_watermark(original_path, i, ii):
    # 创建输出目录
    original_dir = os.path.dirname(original_path)
    output_dir = os.path.join(original_dir, "添加水印")
    os.makedirs(output_dir, exist_ok=True)  # 自动创建目录

    # 生成输出路径
    file_name = os.path.basename(original_path)
    output_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_水印{os.path.splitext(file_name)[1]}")

    # 水印路径配置
    WATERMARKS = {
        "light": r"C:\Users\yyq09\Pictures\水印 - 黑.png",  # 亮背景用黑水印
        "dark": r"C:\Users\yyq09\Pictures\水印 - 白.png"  # 暗背景用白水印
    }

    if os.path.exists(WATERMARKS["light"]) and os.path.exists(WATERMARKS["light"]):
        pass
    else:
        print('水印文件不存在，重新设置水印参数')
        print('水印是否分为黑白两种？ Yes or No')
        water_num = 1 if input().upper() == 'NO' else 2
        if water_num == 2:
            print('输入白色水印文件路径：')
            WATERMARKS["light"] = input()
            print('输入黑色水印文件路径：')
            WATERMARKS["dark"] = input()
        elif water_num == 1:
            print('输入水印文件路径：')
            s_temp = input()
            WATERMARKS["light"], WATERMARKS["dark"] = s_temp, s_temp
        else:
            pass

    # 打开原始图片
    with Image.open(original_path) as img:
        original_format = img.format  # 保留原始格式信息
        # 转换格式并保留Alpha通道
        original = img.convert("RGBA")
        width, height = original.size

        # 计算底部区域亮度（取高度5%的区域）
        crop_height = max(50, int(height * 0.1))
        bottom_region = original.crop((width * 0.45, height - crop_height, width * 0.55, height))
        brightness = calculate_brightness(bottom_region)

        # 选择合适的水印
        watermark_path = WATERMARKS["light"] if brightness > 128 * 1.2 else WATERMARKS["dark"]

        try:
            with Image.open(watermark_path) as watermark:
                # 调整水印尺寸（最大宽度为原图的70%）
                wm_width, wm_height = watermark.size
                if width > height:
                    max_width = int(width * 0.1)
                else:
                    max_width = int(width * 0.17)
                scaling_factor = min(max_width / wm_width, 1.0)

                new_size = (
                    int(wm_width * scaling_factor),
                    int(wm_height * scaling_factor)
                )
                watermark = watermark.resize(new_size, Image.LANCZOS).convert("RGBA")

                # 计算水印位置
                x = (width - new_size[0]) // 2
                y = height - int(new_size[1] * 1.2)  # 底部保留2%边距

                # 创建透明层合并水印
                composite = Image.new("RGBA", original.size)
                composite.paste(watermark, (x, y))
                result = Image.alpha_composite(original, composite)

                # 构建保存参数
                save_params = img.info.copy()

                # 保存结果（保持原始格式）
                # output_path = f"{os.path.splitext(original_path)[0]}_添加水印{os.path.splitext(original_path)[1]}"
                # 修改保存部分
                result.convert(img.mode).save(
                    output_path,
                    format=original_format,
                    **save_params
                )

                print(f"已处理 {i}/{ii}: {os.path.basename(original_path)}")

        except FileNotFoundError:
            print(f"水印文件不存在：{watermark_path}")
        except Exception as e:
            print(f"处理失败：{original_path} - {str(e)}")


if __name__ == "__main__":
    # 支持的图片格式
    extensions = ["jpg", "jpeg", "png", "bmp", "webp"]

    # # 并行处理（提升大图处理速度）
    # with Pool() as pool:
    #     tasks = []
    #     for ext in extensions:
    #         tasks.extend(glob.glob(f"*.{ext}"))
    #     pool.map(add_watermark, tasks)
    i = 1
    for ext in extensions:
        for file in glob.glob(f"*.{ext}"):
            add_watermark(file, i, len(glob.glob(f"*.{ext}")))
            i += 1

    print("处理完成！按回车键退出...")
    input()
