import os
import re
from bs4 import BeautifulSoup
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- 配置 ---
# 强烈建议将 API 密钥设置为环境变量
# 在终端运行: export GOOGLE_API_KEY="你的API密钥"
try:
    GOOGLE_API_KEY = "AIzaSyA4aPmXLMmvGvXpscWUxoRnBk9hrMBiNok"
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY 环境变量未设置")
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"错误：Gemini API密钥配置失败 - {e}")
    # 如果没有密钥，程序仍可运行，但AI调用会失败
    pass

TEMPLATE_DIR = 'cardflow'

# --- FastAPI 应用实例 ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 数据模型 ---
class GenerationRequest(BaseModel):
    system_prompt: str
    template_filename: str | None = None # 改为接收文件名
    user_material: str
    user_dialog: str

# --- 模板分析函数 (我们之前写的脚本) ---
def analyze_template(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    format_tag = "其他"
    style_tag = soup.find('style')
    card_elements = soup.find_all(class_='card')
    if style_tag and style_tag.string:
        style_content = style_tag.string
        freedom_comment = "这行注释代表本排版采取自由模式。"
        card_style_match = re.search(r'\.card\s*\{([^}]+)\}', style_content, re.DOTALL)
        card_styles = card_style_match.group(1) if card_style_match else ""
        if freedom_comment in style_content and 'height: auto' in card_styles:
            format_tag = '自由'
        else:
            aspect_ratio_match = re.search(r'aspect-ratio:\s*([\d\s/]+);', card_styles)
            if aspect_ratio_match:
                ratio = aspect_ratio_match.group(1).strip().replace(' ', '')
                if ratio == '9/16': format_tag = '9:16'
                elif ratio == '16/9': format_tag = '16:9'
                elif ratio == '1/1': format_tag = '1:1'
                elif ratio == '4/3': format_tag = '4:3'
                elif ratio == '3/4': format_tag = '3:4'
            elif 'height: auto' in card_styles and len(card_elements) == 1:
                format_tag = '整体'
    return {"格式": format_tag} # 简化，只返回格式

# --- API 端点 ---

# *** NEW: 新增的端点，用于获取模板列表 ***
@app.get("/templates")
async def get_templates():
    if not os.path.exists(TEMPLATE_DIR):
        return []
    
    templates = []
    for filename in sorted(os.listdir(TEMPLATE_DIR)):
        if filename.endswith('.html'):
            file_path = os.path.join(TEMPLATE_DIR, filename)
            try:
                tags = analyze_template(file_path)
                # 提取一个更友好的名字
                soup = BeautifulSoup(open(file_path, 'r', encoding='utf-8').read(), 'html.parser')
                title = soup.title.string if soup.title else filename
                templates.append({
                    "filename": filename,
                    "display_name": title,
                    "tags": tags
                })
            except Exception as e:
                print(f"分析模板 {filename} 出错: {e}")
    return templates


@app.post("/generate-html")
async def generate_html(request: GenerationRequest):
    template_content = ""
    # *** MODIFIED: 修改逻辑以读取文件 ***
    if request.template_filename:
        try:
            file_path = os.path.join(TEMPLATE_DIR, request.template_filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="模板文件未找到")
    
    try:
        final_prompt = f"""
        {request.system_prompt}

        --- 模板开始 ---
        {template_content}
        --- 模板结束 ---

        --- 用户素材开始 ---
        {request.user_material}
        --- 用户素材结束 ---

        --- 用户要求开始 ---
        {request.user_dialog}
        --- 用户要求结束 ---

        请基于以上所有信息，生成最终的HTML代码。
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=30000
        )
        
        response = await model.generate_content_async(
            final_prompt,
            generation_config=generation_config
        )

        if not response.parts:
            finish_reason = response.candidates[0].finish_reason if response.candidates else "未知"
            error_message = f"Gemini没有返回任何内容。终止原因: {finish_reason}。这可能是由于安全设置或达到了最大长度限制。请尝试修改输入。"
            print(f"错误: {error_message}")
            return {"success": False, "error": error_message}
        
        generated_html = response.text
        
        if "```html" in generated_html:
            generated_html = generated_html.split("```html")[1].split("```")[0]

        return {"success": True, "html": generated_html}

    except Exception as e:
        print(f"发生错误: {e}")
        return {"success": False, "error": str(e)}

# 在终端中运行: uvicorn backend:app --reload
