import os
import re
from pypinyin import pinyin, Style

def chinese_to_pinyin(text):
    """将中文字符串转换为不带空格的小写拼音"""
    pinyin_list = pinyin(text, style=Style.NORMAL)
    return ''.join([item[0] for item in pinyin_list])

def rename_images(folder_path):
    """批量重命名文件夹中的图片文件"""
    # 支持的图片扩展名
    image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 获取文件扩展名
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # 只处理图片文件
        if ext not in image_exts:
            continue
        
        # 匹配文件名开头的数字和短横线（如"01-"）
        match = re.match(r'^\d+\s*-\s*(.*)', name)
        
        if match:
            # 提取数字后面的中文部分
            chinese_part = match.group(1)
        else:
            # 如果没有匹配到数字前缀，使用整个文件名
            chinese_part = name
        
        # 将中文转换为拼音
        pinyin_name = chinese_to_pinyin(chinese_part)
        
        # 构建新文件名
        new_name = f"GFX_goal_{pinyin_name}{ext}"
        
        # 重命名文件
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_name)
        
        # 避免覆盖已存在的文件
        counter = 1
        while os.path.exists(new_path):
            new_name = f"GFX_goal_{pinyin_name}_{counter}{ext}"
            new_path = os.path.join(folder_path, new_name)
            counter += 1
        
        os.rename(old_path, new_path)
        print(f"重命名: {filename} -> {new_name}")

if __name__ == "__main__":
    # 设置要处理的文件夹路径
    folder_path = input("请输入图片文件夹路径: ")
    
    # 验证路径是否存在
    if not os.path.isdir(folder_path):
        print("错误: 指定的路径不是文件夹或不存在")
    else:
        rename_images(folder_path)
        print("\n所有图片重命名完成!")