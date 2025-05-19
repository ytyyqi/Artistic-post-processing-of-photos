from PIL import Image, ImageFilter, ImageDraw, ImageOps, ImageFont
import os


def process_image(image_path, i, output_suffix='_processed'):
    # 打开图片
    img = Image.open(image_path)
    original_format = img.format  # 保留原始格式信息

    if img.mode != 'RGB':
        img = img.convert('RGB')
    w, h = img.size

    if w > h:
        delta_x = max(1, int(w * 0.03))  # 左右各3%
        delta_y_top = max(1, int(h * 0.05))  # 上边5%
        delta_y_bottom = max(1, int(h * 0.15))  # 下边10%
    else:
        delta_x = max(1, int(w * 0.05))  # 左右各3%
        delta_y_top = max(1, int(h * 0.03))  # 上边5%
        delta_y_bottom = max(1, int(h * 0.10))  # 下边10%

    # 计算扩展尺寸
    new_w = w + 2 * delta_x
    new_h = h + delta_y_top + delta_y_bottom

    # 创建扩展背景
    background = Image.new('RGB', (new_w, new_h))

    # 填充上边区域（修改处：移除翻转）
    if delta_y_top > 0:
        top_part = img.crop((0, 0, w, delta_y_top))
        top_resized = top_part.resize((new_w, delta_y_top))  # 直接拉伸
        background.paste(top_resized, (0, 0))

    # 填充下边区域（保持原有翻转逻辑）
    if delta_y_bottom > 0:
        bottom_part = img.crop((0, h - delta_y_bottom, w, h))
        bottom_resized = bottom_part.resize((new_w, delta_y_bottom))
        background.paste(bottom_resized, (0, delta_y_top + h))

    # 填充左右区域（保持原有翻转逻辑）
    if delta_x > 0:
        # 左边
        left_part = img.crop((0, 0, delta_x, h))
        left_resized = left_part.resize((delta_x, h))
        background.paste(left_resized, (0, delta_y_top))

        # 右边
        right_part = img.crop((w - delta_x, 0, w, h))
        right_resized = right_part.resize((delta_x, h))
        background.paste(right_resized, (w + delta_x, delta_y_top))

    # 粘贴原图到中间
    background.paste(img, (delta_x, delta_y_top))

    # 高斯模糊
    background = background.filter(ImageFilter.GaussianBlur(radius=69))

    # 将浮雕图覆盖到背景
    background.paste(img, (delta_x, delta_y_top))

    # 构建保存参数
    save_params = img.info.copy()

    # 保存结果
    base, ext = os.path.splitext(image_path)
    output_path = f"{base}_高斯背景{ext}"
    # 创建输出目录
    os.makedirs('高斯背景', exist_ok=True)  # 自动创建目录
    background.save(
        '高斯背景//' + output_path,
        format=original_format,
        **save_params
    )
    print(f"Success {i}/All: {output_path}")


if __name__ == "__main__":
    i = 1
    # 遍历当前目录下的所有图片文件
    for filename in os.listdir('.'):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            process_image(filename, i)
            i += 1

    print("处理完成！按回车键退出...")
    input()
