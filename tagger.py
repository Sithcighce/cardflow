import os
import re
from bs4 import BeautifulSoup

def analyze_template(file_path):
    """
    Analyzes a single HTML template file to extract its format and color scheme
    based on a specific set of rules.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    
    # --- 1. Extract Format (格式) ---
    format_tag = "其他"  # 默认格式
    style_tag = soup.find('style')
    card_elements = soup.find_all(class_='card')

    if style_tag and style_tag.string:
        style_content = style_tag.string
        
        # 定义“自由”格式必须包含的特定注释
        freedom_comment = "这行注释代表本排版采取自由模式。Card采用定宽变高，每一个Card必须合理控制文字，使得高宽比介于9：16 ~ 16：9之间。"

        # 提取 .card 的样式块
        card_style_match = re.search(r'\.card\s*\{([^}]+)\}', style_content, re.DOTALL)
        card_styles = ""
        if card_style_match:
            card_styles = card_style_match.group(1)

        # --- 按优先级顺序应用规则 ---
        
        # 规则 1: 检验是否为“自由”格式 (必须同时满足注释和 height: auto)
        if freedom_comment in style_content and 'height: auto' in card_styles:
            format_tag = '自由'
        else:
            # 规则 2: 如果不是“自由”，则检查固定比例
            aspect_ratio_match = re.search(r'aspect-ratio:\s*([\d\s/]+);', card_styles)
            if aspect_ratio_match:
                ratio = aspect_ratio_match.group(1).strip()
                if ratio == '9 / 16': format_tag = '9:16'
                elif ratio == '16 / 9': format_tag = '16:9'
                elif ratio == '1 / 1': format_tag = '1:1'
                elif ratio == '4 / 3': format_tag = '4:3'
                elif ratio == '3 / 4': format_tag = '3:4'
            
            # 规则 3: 如果也不是固定比例，则检查是否为“整体”格式
            elif 'height: auto' in card_styles and len(card_elements) == 1:
                format_tag = '整体'
            
            # 规则 4: 如果以上都不是，则格式为“其他” (已是默认值)

    # --- 2. Extract Colors (配色) ---
    color_tags = set()
    if style_tag and style_tag.string:
        # 这个正则表达式会查找 .card 和其内部常见元素的样式块
        relevant_styles = re.findall(r'(\.card[^{,]*|h\d[^{,]*|p[^{,]*|li[^{,]*|blockquote[^{,]*)\s*\{([^}]+)\}', style_tag.string, re.DOTALL)
        
        # 优先查找卡片背景色
        for selector, styles in relevant_styles:
            if selector.strip() == '.card':
                bg_match = re.search(r'background-color:\s*#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})', styles)
                if bg_match:
                    color_tags.add(f"#{bg_match.group(1).upper()}")
                break

        # 查找其他文本和重点颜色
        for selector, styles in relevant_styles:
            if any(keyword in selector for keyword in ['button', 'pagination', 'body']):
                continue
            
            # 查找 color, background-color, 和各种 border-color 属性
            colors_in_block = re.findall(r'(?:color|background-color|border-color|border-bottom-color|border-top-color):\s*#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})', styles)
            for color in colors_in_block:
                color_tags.add(f"#{color.upper()}")

    final_colors = sorted(list(color_tags))
    
    return {
        "配色": final_colors,
        "格式": format_tag
    }

def main():
    """
    主函数，用于遍历目录中的HTML文件并打印其标签。
    """
    directory = 'cardflow'
    if not os.path.exists(directory):
        print(f"错误：找不到文件夹 '{directory}'。请确保您的HTML文件位于该文件夹中。")
        return

    print("--- 模板标签分析结果 ---\n")
    
    html_files = sorted([f for f in os.listdir(directory) if f.endswith('.html')])

    for filename in html_files:
        file_path = os.path.join(directory, filename)
        try:
            tags = analyze_template(file_path)
            print(f"📄 文件: {filename}")
            print(f"   🎨 配色 = {tags['配色']}")
            print(f"   📐 格式 = {tags['格式']}")
            print("-" * 25)
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")

if __name__ == "__main__":
    main()
