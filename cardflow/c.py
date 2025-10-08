import os
import re

def remove_script_tags_in_folder(folder_path, file_extensions=None):
    """
    遍历 folder_path 下的所有文件，删除文件内容中所有 <script>...</script> 块，
    并打印出每个文件中被删除的脚本内容。

    参数:
        folder_path (str): 目标文件夹路径。
        file_extensions (set of str, optional): 需要处理的文件扩展名（不含点），
            例如 {'html', 'htm'}。若为 None，则处理所有文件。
    """
    # 用于匹配 <script> 标签及其内部所有内容（包括多行）
    script_pattern = re.compile(r'<script\b[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)

    for root, _, files in os.walk(folder_path):
        for filename in files:
            ext = filename.rsplit('.', 1)[-1].lower()
            if file_extensions is None or ext in file_extensions:
                file_path = os.path.join(root, filename)

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 找出所有待删除的 <script> 块
                matches = script_pattern.findall(content)
                if matches:
                    print(f'文件: {file_path}')
                    for i, script_block in enumerate(matches, start=1):
                        # 如脚本内容过长，可根据需要截断或省略中间部分
                        preview = script_block.strip().replace('\n', ' ')[:200]
                        print(f'  [{i}] 删除内容预览: {preview}{"…" if len(script_block) > 200 else ""}')

                    # 真正执行删除
                    new_content = script_pattern.sub('', content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    print(f'  ✅ 共删除 {len(matches)} 个 <script> 块\n')
