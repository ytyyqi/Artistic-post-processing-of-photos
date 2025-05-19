import os
from PIL import Image

supported_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']


def find_image_file(filename):
    """查找实际存在的图片文件（支持无扩展名或错误扩展名）"""
    # 如果输入包含扩展名
    if os.path.splitext(filename)[1]:
        if os.path.isfile(filename):
            return filename
        # 尝试纠正大小写
        base = os.path.splitext(filename)[0]
        for ext in supported_extensions:
            if os.path.isfile(base + ext.lower()):
                return base + ext.lower()
    # 无扩展名的情况
    else:
        for ext in supported_extensions:
            path = filename + ext
            if os.path.isfile(path):
                return path
    return None


def main():
    images = []
    original_filenames = []
    max_width = 0

    print("""照片拼接工具
==========================
1. 输入图片名称
2. 输入 'done' 完成输入
3. 输入 'exit' 退出程序
""")

    while True:
        user_input = input("请输入图片名称 > ").strip()

        # 退出检测
        if user_input.lower() == 'exit':
            print("已退出程序")
            return

        # 完成输入检测
        if not user_input or user_input.lower() == 'done':
            if not images:
                print("错误：至少需要输入一张有效图片")
                continue
            break

        # 查找文件
        filepath = find_image_file(user_input)
        if not filepath:
            print(f" × 未找到文件: {user_input}（支持格式：{', '.join(supported_extensions)}）")
            continue

        # 加载图片
        try:
            img = Image.open(filepath)
            img = img.convert('RGB')
            images.append(img)
            original_filenames.append(os.path.basename(filepath))
            max_width = max(max_width, img.width)
            print(f" √ 已加载: {filepath} ({img.width} x {img.height})")
        except Exception as e:
            print(f" × 无法处理文件 {filepath}: {str(e)}")
            continue

    # 调整图片尺寸
    resized_images = []
    total_height = 0
    print("\n正在调整图片尺寸...")
    for img in images:
        w_percent = max_width / img.width
        h_size = int(img.height * w_percent)
        resized_img = img.resize((max_width, h_size), Image.LANCZOS)
        resized_images.append(resized_img)
        total_height += h_size
        print(f" → 调整 {img.width} x {img.height} 到 {max_width} x {h_size}")

    # 拼接图片
    combined_img = Image.new('RGB', (max_width, total_height))
    y_offset = 0
    info_data = []

    print("\n开始拼接图片...")
    for i, img in enumerate(resized_images):
        combined_img.paste(img, (0, y_offset))
        info_data.append({
            'filename': original_filenames[i],
            'y_start': y_offset,
            'height': img.height
        })
        print(f" ✓ 已拼接: {original_filenames[i]} (起始位置: {y_offset}, 高度: {img.height})")
        y_offset += img.height

    # 保存结果
    combined_img.save('combined.jpg')
    with open('combined_info.txt', 'w') as f:
        for entry in info_data:
            f.write(f"{entry['filename']},{entry['y_start']},{entry['height']}\n")

    print(f"""\n操作完成！
生成文件：combined.jpg（尺寸：{max_width}x{total_height}）
         combined_info.txt（包含 {len(info_data)} 条记录）""")


if __name__ == "__main__":
    main()

    print("处理完成！按回车键退出...")
    aaa = input()
