from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import glob
# from multiprocessing import Pool
from PIL.ExifTags import TAGS
import piexif
from rich.progress import Progress

# 新增字体路径配置（微软雅黑）
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"  # Windows系统字体路径


def get_exif_data(img):
    """获取EXIF信息并解析关键参数"""
    exif_data = {}
    try:
        if hasattr(img, '_getexif'):
            exif_info = img._getexif()
            if exif_info:
                for tag, value in exif_info.items():
                    decoded = TAGS.get(tag, tag)
                    exif_data[decoded] = value

        # 使用piexif补充读取（兼容更多格式）
        exif_dict = piexif.load(img.info.get('exif', b''))
        for ifd in exif_dict:
            for tag in exif_dict[ifd]:
                tag_name = piexif.TAGS[ifd][tag]["name"]
                exif_data[tag_name] = exif_dict[ifd][tag]
    except:
        pass

    # 参数解析逻辑
    def parse_param(param):
        if isinstance(param, tuple):
            return float(param[0]) / float(param[1])
        elif isinstance(param, int):
            return float(param)
        return None

    # 焦距处理
    focal_length = exif_data.get('FocalLength', exif_data.get('FocalLengthIn35mmFilm'))
    focal = f"{int(parse_param(focal_length))}mm" if focal_length else '--mm'

    # 光圈处理
    aperture = exif_data.get('FNumber', exif_data.get('ApertureValue'))
    f_number = f"f/{parse_param(aperture):.1f}" if aperture else 'f/--'

    # 快门速度处理
    exposure = exif_data.get('ExposureTime')
    if exposure:
        if isinstance(exposure, tuple):
            val = parse_param(exposure)
            shutter = f"1/{int(1 / val)}s" if val < 1 else f"{val:.0f}s"
        else:
            shutter = f"{exposure}s"
    else:
        shutter = '--s'

    # ISO处理
    iso = exif_data.get('ISOSpeedRatings', exif_data.get('PhotographicSensitivity'))
    iso_str = f"ISO{iso}" if iso else 'ISO---'

    return f"{focal}   {f_number}   {shutter}   {iso_str}"


def calculate_brightness(img):
    """计算图片区域的平均亮度"""
    pixels = img.convert("L").getdata()
    return sum(pixels) / len(pixels)


def add_watermark(original_path, i, ii):
    # 创建输出目录
    original_dir = os.path.dirname(original_path)
    output_dir = os.path.join(original_dir, "添加水印和拍摄信息")
    os.makedirs(output_dir, exist_ok=True)  # 自动创建目录

    # 生成输出路径
    file_name = os.path.basename(original_path)
    output_path = os.path.join(output_dir,
                               f"{os.path.splitext(file_name)[0]}_水印和拍摄信息{os.path.splitext(file_name)[1]}")

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
                    FONT_RATIO = 0.25  # 文字大小与水印高度的比例
                    TEXT_MARGIN = 17  # 水印与文字间距
                    down_length = 1.5  # 底边距离
                else:
                    max_width = int(width * 0.17)
                    FONT_RATIO = 0.25  # 文字大小与水印高度的比例
                    TEXT_MARGIN = 20  # 水印与文字间距
                    down_length = 1.5  # 底边距离
                scaling_factor = min(max_width / wm_width, 1.0)

                new_size = (
                    int(wm_width * scaling_factor),
                    int(wm_height * scaling_factor)
                )
                watermark = watermark.resize(new_size, Image.LANCZOS).convert("RGBA")

                # 计算水印位置
                x = (width - new_size[0]) // 2
                y = height - int(new_size[1] * down_length)  # 底部保留边距

                # 创建透明层合并水印
                composite = Image.new("RGBA", original.size)
                composite.paste(watermark, (x, y))
                result = Image.alpha_composite(original, composite)

                # 在合成水印后添加文字信息
                exif_text = get_exif_data(img)
                draw = ImageDraw.Draw(result)

                # 自动选择字体大小（水印高度的40%）
                text_size = int(new_size[1] * FONT_RATIO)
                try:
                    # 尝试加载微软雅黑字体
                    font = ImageFont.truetype(FONT_PATH, text_size)
                except Exception as e:
                    print(f"字体加载失败，使用默认字体：{str(e)}")
                    font = ImageFont.load_default(text_size)

                # 计算文字位置（水印下方10像素）
                text_y = y + new_size[1] + TEXT_MARGIN
                text_width = font.getlength(exif_text)
                text_x = (width - text_width) // 2

                # 自动选择文字颜色（基于水印区域亮度）
                text_color = 'white' if calculate_brightness(bottom_region) < 128 * 1.2 else 'black'

                # 添加文字阴影增强可读性
                shadow_color = 'white' if text_color == 'white' else 'black'
                for offset in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    draw.text((text_x + offset[0], text_y + offset[1]),
                              exif_text, font=font, fill=shadow_color)

                # 绘制主文字
                draw.text((text_x, text_y), exif_text, font=font, fill=text_color)

                # 构建保存参数
                save_params = img.info.copy()

                # 保存结果（保持原始格式）
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
