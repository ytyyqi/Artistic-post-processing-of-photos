from PIL import Image, ImageFilter, ImageDraw, ImageFont
import piexif
import os
from rich.progress import Progress

# Configuration constants
WATERMARKS = {
    "light": r"C:\Users\yyq09\Pictures\水印 - 黑.png",
    "dark": r"C:\Users\yyq09\Pictures\水印 - 白.png"
}
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"
OUTPUT_DIRS = {
    "background": "高斯背景",
    "final": "信息模糊水印处理"
}
BLUR_RADIUS = 69
BRIGHTNESS_THRESHOLD = 128 * 1.2


def apply_drop_shadow(
        background: Image.Image,
        img: Image.Image,
        position: tuple[int, int]
) -> None:
    shadow_radius = int(min(img.size) * 0.015)
    shadow_opacity = 255

    """为图片添加阴影效果   

    Args:
        background: 背景画布对象
        img: 原始图片对象
        position: 图片粘贴位置 (x, y)
        shadow_radius: 阴影扩散半径（默认10像素）
        shadow_opacity: 阴影透明度（0-255，默认80）
    """

    x, y = position
    width, height = img.size

    # 创建阴影层
    shadow_layer = Image.new("RGBA", (width + shadow_radius * 2, height + shadow_radius * 2))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    # 绘制渐变阴影
    for i in range(shadow_radius, 0, -1):
        alpha = int(shadow_opacity * (shadow_radius / shadow_radius) ** 0.8)
        shadow_draw.rounded_rectangle(
            [(shadow_radius - i, shadow_radius - i),
             (width + shadow_radius + i - 1, height + shadow_radius + i - 1)],
            radius=int(min(width, height) * 0.03) + i,
            fill=(0, 0, 0, alpha))

    # 粘贴阴影到背景
    background.paste(shadow_layer, (x - shadow_radius, y - shadow_radius), shadow_layer)


def add_rounded_corners(img: Image.Image, radius: int = 15) -> Image.Image:
    """为图片添加圆角效果

    Args:
        img: 原始图片对象
        radius: 圆角半径（默认15像素）

    Returns:
        PIL.Image.Image: 带圆角的图片对象
    """
    # 创建透明蒙版
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)

    # 绘制圆角矩形
    draw.rounded_rectangle([(0, 0), img.size], radius, fill=255)

    # 应用蒙版
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    img.putalpha(mask)
    return img


def process_image(image_path: str, index, ii) -> Image.Image:
    """为图片添加高斯模糊背景

    Args:
        image_path: 原始图片路径
        index: 当前处理序号

    Returns:
        PIL.Image.Image: 处理后的图片对象
    """
    with Image.open(image_path) as img:
        original_format = img.format
        img = img.convert("RGB") if img.mode != "RGB" else img
        width, height = img.size

        # 计算扩展尺寸
        is_landscape = width > height
        delta_x = calculate_padding(width, 0.03 if is_landscape else 0.05)
        delta_y_top = calculate_padding(height, 0.05 if is_landscape else 0.03)
        delta_y_bottom = calculate_padding(height, 0.12 if is_landscape else 0.08)

        new_width = width + 2 * delta_x
        new_height = height + delta_y_top + delta_y_bottom

        # 创建背景画布
        background = create_background(img, new_width, new_height, delta_x, delta_y_top, delta_y_bottom)

        # 应用高斯模糊
        blurred_background = background.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))

        rounded_img = add_rounded_corners(img.copy(), radius=int(min(width, height) * 0.035))  # 自适应圆角大小
        blurred_background.paste(rounded_img, (delta_x, delta_y_top), rounded_img)  # 添加蒙版参数

        print(f"背景处理 {index}/{ii}: {os.path.basename(image_path)}")
        return blurred_background


def calculate_padding(dimension: int, ratio: float) -> int:
    """计算扩展边距"""
    return max(1, int(dimension * ratio))


def create_background(
        img: Image.Image,
        new_width: int,
        new_height: int,
        delta_x: int,
        delta_y_top: int,
        delta_y_bottom: int
) -> Image.Image:
    """创建扩展背景画布"""
    background = Image.new("RGB", (new_width, new_height))
    width, height = img.size

    # 填充顶部区域
    if delta_y_top > 0:
        top_section = img.crop((0, 0, width, delta_y_top))
        background.paste(top_section.resize((new_width, delta_y_top)), (0, 0))

    # 填充底部区域
    if delta_y_bottom > 0:
        bottom_section = img.crop((0, height - delta_y_bottom, width, height))
        background.paste(bottom_section.resize((new_width, delta_y_bottom)),
                         (0, delta_y_top + height))

    # 填充两侧区域
    if delta_x > 0:
        # 左侧
        left_section = img.crop((0, 0, delta_x, height))
        background.paste(left_section.resize((delta_x, height)), (0, delta_y_top))

        # 右侧
        right_section = img.crop((width - delta_x, 0, width, height))
        background.paste(right_section.resize((delta_x, height)),
                         (width + delta_x, delta_y_top))

    # 添加阴影效果
    apply_drop_shadow(background, img, (delta_x, delta_y_top))

    # 粘贴原图到中心
    background.paste(img, (delta_x, delta_y_top))
    return background


def get_exif_data(img: Image.Image) -> str:
    """从图片中提取EXIF信息"""
    exif_info = {}
    try:
        # 通过piexif获取完整EXIF数据
        exif_dict = piexif.load(img.info.get("exif", b""))
        for ifd in ("0th", "Exif", "GPS", "1st"):
            for tag, value in exif_dict.get(ifd, {}).items():
                tag_name = piexif.TAGS[ifd][tag]["name"]
                exif_info[tag_name] = value
    except Exception:
        pass

    # 解析拍摄参数
    focal_length = parse_exif_value(
        exif_info.get("FocalLength", exif_info.get("FocalLengthIn35mmFilm")))
    aperture = parse_exif_value(exif_info.get("FNumber"))
    exposure = parse_exif_value(exif_info.get("ExposureTime"))
    iso = parse_exif_value(exif_info.get("ISOSpeedRatings", exif_info.get("PhotographicSensitivity")))

    # 格式化输出字符串
    return format_exif_string(focal_length, aperture, exposure, iso)


def parse_exif_value(value) -> float:
    """解析EXIF数值"""
    if isinstance(value, tuple):
        return float(value[0]) / float(value[1])
    if isinstance(value, (int, float)):
        return float(value)
    return None


def format_exif_string(focal: float, aperture: float, exposure: float, iso: float) -> str:
    """格式化EXIF信息为字符串"""
    focal_str = f"{int(focal)}mm" if focal else "--mm"
    aperture_str = f"f/{aperture:.1f}" if aperture else "f/--"

    if exposure:
        shutter = f"1/{int(1 / exposure)}s" if exposure < 1 else f"{exposure:.0f}s"
    else:
        shutter = "--s"

    iso_str = f"ISO{int(iso)}" if iso else "ISO---"

    return f"{focal_str}   {aperture_str}   {shutter}   {iso_str}"


def calculate_brightness(img: Image.Image) -> float:
    """计算图片区域的平均亮度"""
    gray_img = img.convert("L")
    pixels = list(gray_img.getdata())
    return sum(pixels) / len(pixels)


def add_watermark(
        background_img: Image.Image,
        original_path: str,
        index, ii
) -> None:
    """为图片添加水印和EXIF信息

    Args:
        background_img: 背景处理后的图片对象
        original_path: 原始图片路径
        index: 当前处理序号
    """
    try:
        with Image.open(original_path) as original_img:
            output_dir = os.path.join(os.getcwd(), OUTPUT_DIRS["final"])
            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(
                output_dir,
                f"{os.path.splitext(os.path.basename(original_path))[0]}_信息模糊水印处理"
                f"{os.path.splitext(original_path)[1]}"
            )

            # 准备透明图层
            rgba_image = background_img.convert("RGBA")
            width, height = rgba_image.size

            # 检测底部亮度
            crop_height = max(50, int(height * 0.1))
            bottom_region = rgba_image.crop((
                width * 0.45,
                height - crop_height,
                width * 0.55,
                height
            ))
            brightness = calculate_brightness(bottom_region)

            # 选择水印类型
            watermark_type = "light" if brightness > BRIGHTNESS_THRESHOLD else "dark"
            watermark_img = load_watermark_image(
                WATERMARKS[watermark_type],
                width,
                height
            )

            # 合成水印
            composite_image = composite_watermark(rgba_image, watermark_img)

            # 添加文字信息
            final_image = add_exif_text(
                composite_image,
                original_img,
                watermark_img.size,
                watermark_type
            )

            # 保存结果
            final_image.convert(original_img.mode).save(
                output_path,
                format=original_img.format,
                **original_img.info
            )

            print(f"水印处理 {index}/{ii}: {os.path.basename(original_path)}")

    except Exception as e:
        print(f"处理失败: {original_path} - {str(e)}")


def load_watermark_image(path: str, img_width: int, img_height: int) -> Image.Image:
    """加载并调整水印尺寸"""
    with Image.open(path) as watermark:
        max_width = img_width * 0.1 if img_width > img_height else img_width * 0.13
        scaling_factor = min(max_width / watermark.width, 1.0)
        return watermark.resize(
            (int(watermark.width * scaling_factor),
             int(watermark.height * scaling_factor)),
            Image.LANCZOS
        ).convert("RGBA")


def composite_watermark(base_img: Image.Image, watermark: Image.Image) -> Image.Image:
    """合成水印到基础图片"""
    if base_img.width > base_img.height:
        position = (
            (base_img.width - watermark.width) // 2,
            base_img.height - int(watermark.height * 1.43)
        )
    else:
        position = (
            (base_img.width - watermark.width) // 2,
            base_img.height - int(watermark.height * 1.6)
        )

    composite = Image.new("RGBA", base_img.size)
    composite.paste(watermark, position, watermark)
    return Image.alpha_composite(base_img, composite)


def add_exif_text(
        image: Image.Image,
        original_img: Image.Image,
        watermark_size: tuple,
        watermark_type: str
) -> Image.Image:
    """添加EXIF文字信息"""
    draw = ImageDraw.Draw(image)
    exif_text = get_exif_data(original_img)

    # 计算文字参数
    text_size = int(watermark_size[1] * 0.25)
    try:
        font = ImageFont.truetype(FONT_PATH, text_size)
    except IOError:
        font = ImageFont.load_default(text_size)

    # 文字位置计算
    text_y = image.height - int(image.height * 0.027) if image.width > image.height else image.height - int(
        image.height * 0.025)
    text_width = font.getlength(exif_text)
    text_x = (image.width - text_width) // 2

    # 文字颜色设置
    text_color = "white" if watermark_type == "dark" else "black"
    shadow_color = "black" if text_color == "white" else "white"

    # 添加文字阴影
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        draw.text((text_x + dx, text_y + dy), exif_text, font=font, fill=shadow_color)

    # 添加主文字
    draw.text((text_x, text_y), exif_text, font=font, fill=text_color)
    return image


if __name__ == "__main__":
    supported_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
    image_files = [
        f for f in os.listdir(".")
        if f.lower().endswith(supported_extensions)
    ]

    i = 1
    for idx, filename in enumerate(image_files, 1):
        processed_bg = process_image(filename, i, len(image_files))
        add_watermark(processed_bg, filename, i, len(image_files))
        i += 1

    print("处理完成！按回车键退出...")
    input()
