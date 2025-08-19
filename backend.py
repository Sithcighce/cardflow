import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

# --- 配置 ---
# 强烈建议将 API 密钥设置为环境变量，而不是硬编码
# 在终端运行: export GOOGLE_API_KEY="你的API密钥"
GOOGLE_API_KEY = 'AIzaSyA4aPmXLMmvGvXpscWUxoRnBk9hrMBiNok'
genai.configure(api_key=GOOGLE_API_KEY)

# --- FastAPI 应用实例 ---
app = FastAPI()

# 允许来自 Electron App 的跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有来源，本地开发时足够安全
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 数据模型 ---
# 定义从前端接收的数据结构
class GenerationRequest(BaseModel):
    system_prompt: str
    template_content: str
    user_material: str
    user_dialog: str

# --- API 端点 ---
@app.post("/generate-html")
async def generate_html(request: GenerationRequest):
    """
    接收前端请求，调用 Gemini API，并返回生成的 HTML。
    """
    try:
        # 1. 拼接最终的 Prompt
        final_prompt = f"""
        {request.system_prompt}

        --- 模板开始 ---
        {request.template_content}
        --- 模板结束 ---

        --- 用户素材开始 ---
        {request.user_material}
        --- 用户素材结束 ---

        --- 用户要求开始 ---
        {request.user_dialog}
        --- 用户要求结束 ---
        """

        # 2. 调用 Gemini API
        model = genai.GenerativeModel('gemini-1.5-flash') # 或者使用 gemini-1.5-pro
        response = await model.generate_content_async(final_prompt)

        generated_html = response.text

        # 简单的清洗，移除 Gemini 可能添加的代码块标记
        if "```html" in generated_html:
            generated_html = generated_html.split("```html")[1].split("```")[0]

        return {"success": True, "html": generated_html}

    except Exception as e:
        print(f"发生错误: {e}")
        return {"success": False, "error": str(e)}

# --- 启动服务器 ---
# 在终端中运行: uvicorn backend:app --reload