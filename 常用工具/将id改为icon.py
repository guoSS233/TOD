import re

def modify_file(input_file, output_file=None):
    """
    修改文件内容，将icon后面的值改为id后面的值
    
    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径(可选，如果为None则修改原文件)
    """
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式匹配id和icon行
    pattern = re.compile(r'id\s*=\s*(\w+).*?\n\s*icon\s*=\s*(\w+)', re.DOTALL)
    
    # 替换icon值为id值
    modified_content = pattern.sub(lambda m: m.group(0).replace(m.group(2), m.group(1)), content)
    
    # 决定输出到新文件还是覆盖原文件
    if output_file is None:
        output_file = input_file
    
    # 写入修改后的内容
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python 将id改为icon.py.py <输入文件> [输出文件]")
        print("如果未指定输出文件，将直接修改输入文件")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    modify_file(input_file, output_file)
    print("文件修改完成!")