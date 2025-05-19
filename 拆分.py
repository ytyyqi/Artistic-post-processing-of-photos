import os
from PIL import Image
import warnings

warnings.filterwarnings("ignore")


def main():
    # 自动检测文件路径
    combined_img_path = 'combined.jpg'
    info_file_path = 'combined_info.txt'

    print("""\n照片拆分工具（自动模式）
==========================
检测当前目录下的：
- 拼接文件：combined.jpg
- 信息文件：combined_info.txt
""")

    # 验证文件存在
    if not os.path.exists(combined_img_path):
        print(f"错误：找不到拼接文件 {combined_img_path}")
        return

    if not os.path.exists(info_file_path):
        print(f"错误：找不到信息文件 {info_file_path}")
        return

    try:
        # 加载拼接图片
        combined_img = Image.open(combined_img_path)
        img_width = combined_img.width
        print(f"√ 已加载拼接图片 ({img_width}x{combined_img.height})")
    except Exception as e:
        print(f"无法打开拼接图片: {e}")
        return

    try:
        # 读取信息文件
        with open(info_file_path) as f:
            lines = f.readlines()
        print(f"√ 已加载信息文件（包含 {len(lines)} 条记录）")
    except Exception as e:
        print(f"无法打开信息文件: {e}")
        return

    success_count = 0
    error_count = 0

    print("\n开始拆分图片...")
    for line_num, line in enumerate(lines, 1):
        parts = line.strip().split(',')
        if len(parts) != 3:
            print(f"× 第{line_num}行格式错误：{line.strip()}")
            error_count += 1
            continue

        filename, y_start, height = parts
        try:
            y = int(y_start)
            h = int(height)
        except ValueError:
            print(f"× 第{line_num}行数值错误：{line.strip()}")
            error_count += 1
            continue

        # 验证坐标有效性
        if y < 0 or h <= 0:
            print(f"× 第{line_num}行数值无效（y={y}, h={h}）")
            error_count += 1
            continue

        if y + h > combined_img.height:
            print(f"× 第{line_num}行越界：{y + h} > 图片总高度 {combined_img.height}")
            error_count += 1
            continue

        # 创建输出目录（如果需要）
        # Create a single directory
        path = "拆分图片"
        if not os.path.exists(path):
            os.makedirs(path)


        # 执行裁剪
        try:
            crop_area = (0, y, img_width, y + h)
            cropped = combined_img.crop(crop_area)
            cropped.save('拆分图片//' + filename)
            print(f"√ 已保存：{filename} ({img_width}x{h})")
            success_count += 1
        except Exception as e:
            print(f"× 保存 {filename} 失败：{str(e)}")
            error_count += 1

    print(f"""\n操作完成！
成功拆分：{success_count} 张
失败记录：{error_count} 条""")


if __name__ == "__main__":
    main()

    print("处理完成！按回车键退出...")
    aaa = input()
