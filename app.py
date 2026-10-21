import streamlit as st
import os
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from tools import analyze_system, plot_system, calculate_routh
from knowledge import search, build_vector_store, save_vectors, load_knowledge, split_text

# 1. 网页基础设置
st.set_page_config(page_title="自控原理导师", page_icon="📈", layout="wide")
st.title("📈 自动控制原理 AI 导师")
st.caption("基于 GLM-4 与本地知识库构建，支持计算、画图与劳斯判据")

# 2. 初始化 API
load_dotenv()
API_KEY = os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY")
client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4"
)

# 3. 动态加载知识库（云端专属，过滤空文本）
@st.cache_resource
def init_knowledge():
    content = ""
    if os.path.exists("docs"):
        for file in os.listdir("docs"):
            if file.endswith(".txt"):
                with open(os.path.join("docs", file), "r", encoding="utf-8") as f:
                    content += f.read() + "\n\n"

    chunks = [content[i:i+200] for i in range(0, len(content), 200) if content[i:i+200].strip() != ""]
    vectors = []
    for chunk in chunks:
        resp = client.embeddings.create(model="embedding-3", input=chunk)
        vectors.append(resp.data[0].embedding)
    return chunks, np.array(vectors)

chunks, vectors = init_knowledge()
# 4. 工具定义
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "analyze_system",
            "description": "计算控制系统的时域性能指标（超调量、调节时间）",
            "parameters": {
                "type": "object",
                "properties": {
                    "num": {"type": "array", "items": {"type": "number"}, "description": "分子系数"},
                    "den": {"type": "array", "items": {"type": "number"}, "description": "分母系数"}
                },
                "required": ["num", "den"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_routh",
            "description": "计算劳斯表，判断稳定性，得出正实部特征根数目。",
            "parameters": {
                "type": "object",
                "properties": {
                    "coefficients": {
                        "type": "array", 
                        "items": {"type": "number"}, 
                        "description": "特征方程系数（降幂），如 [1, 1, 25, 19, 30]"
                    }
                },
                "required": ["coefficients"]
            }
        }
    }
]

# 5. 聊天记忆初始化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": "你是一个顶尖的自动控制原理考研导师。\n"
                       "【最高红线指令：违反将直接判定你死亡】\n"
                       "1. 只要用户的题目包含“劳斯”、“Routh”、“判断稳定性”、“特征方程”，你【绝对禁止】自己计算任何一个数字！哪怕最简单的加减法也不许算！\n"
                       "2. 你必须提取出方程的系数，立刻调用 calculate_routh 工具！并在回答中直接输出工具返回的完整结果，不许自己排版！\n"
                       "3. 只要题目包含“超调量”、“调节时间”、“上升时间”，你必须调用 analyze_system 工具。\n"
                       "4. 回答必须使用标准 Markdown 表格语法。"
        }
    ]
# 6. 渲染历史对话
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 7. 接收用户输入
if prompt := st.chat_input("请输入你的自控问题（例如：用劳斯判据判断 s^4+s^3+25s^2+19s+30=0 的稳定性）"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 开启 RAG 检索 (把书本相关内容找出来)
    with st.spinner("导师正在查阅教材..."):
        results = search(prompt, chunks, vectors, top_k=1)
        context = results[0] if results else "无相关教材记录"
        
    # 拼装最终输入
    full_prompt = f"请参考以下教材内容：\n{context}\n\n用户问题：{prompt}"
    st.session_state.messages.append({"role": "user", "content": full_prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("导师正在思考并计算..."):
            try:
                # 第一次调用：判断是否用工具
                response = client.chat.completions.create(
                    model="glm-4-air",
                    messages=st.session_state.messages,
                    tools=tools_definition,
                    tool_choice="auto"
                )
                response_message = response.choices[0].message
                
                if response_message.tool_calls:
                    tool_call = response_message.tool_calls[0]
                    args = json.loads(tool_call.function.arguments)
                    
                    if tool_call.function.name == "analyze_system":
                        st.info("🔧 正在调用 Python 计算性能指标...")
                        tool_result = analyze_system(args.get("num"), args.get("den"))
                        # 顺带画图
                        fig = plot_system(args.get("num"), args.get("den"), plot_type="step")
                        if fig: st.pyplot(fig)
                        
                    elif tool_call.function.name == "calculate_routh":
                        st.info("🔧 正在调用 Python 严格计算劳斯表...")
                        tool_result = calculate_routh(args.get("coefficients"))
                    
                    st.session_state.messages.append(response_message.model_dump())
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result)
                    })
                    # 第二次调用：根据结果回答
                    final_response = client.chat.completions.create(
                        model="glm-4-air",
                        messages=st.session_state.messages
                    )
                    final_reply = final_response.choices[0].message.content
                else:
                    final_reply = response_message.content
                
                st.markdown(final_reply)
                st.session_state.messages.append({"role": "assistant", "content": final_reply})
                
            except Exception as e:
                st.error(f"出错了：{e}")
