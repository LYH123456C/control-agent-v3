from tools import analyze_system, plot_system
import streamlit as st
import os
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from tools import analyze_system
from knowledge import load_chunks_and_vectors

# 1. 网页基础设置
st.set_page_config(page_title="自控原理导师", page_icon="📈", layout="wide")
st.title("📈 自动控制原理 AI 导师")
st.caption("基于 GLM-4 与 Python 控制库构建，支持传递函数自动计算")

# 2. 加载知识库（获取切分好的文档和向量）

with st.sidebar:
    st.header("⚙️ 控制面板")
    st.write("当前模型：GLM-4-Air")
    if st.button("🗑️ 清空对话记忆"):
        st.session_state.messages = [
            {"role": "system", "content": "你是一个顶尖的自动控制原理考研导师。回答概念时，必须严谨、通俗，使用考研的标准术语。如果用户给出传递函数要求分析性能指标，你必须调用 analyze_system 工具进行计算。如果用户要求画图，请输出 MATLAB 代码。绝对不要废话。"}
        ]
        st.rerun()

# 3. 初始化 API
load_dotenv()
API_KEY = os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY")
client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4"
)
import numpy as np

# 动态加载并生成知识库向量
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
vectors = np.array(vectors)

# 4. 工具定义
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "analyze_system",
            "description": "计算二阶或高阶系统的时域性能指标（超调量、调节时间等）",
            "parameters": {
                "type": "object",
                "properties": {
                    "num": {"type": "array", "items": {"type": "number"}, "description": "传递函数分子系数，例如 [10]"},
                    "den": {"type": "array", "items": {"type": "number"}, "description": "传递函数分母系数，例如 [1, 2, 10]"}
                },
                "required": ["num", "den"]
            }
        }
    }
]

# 5. 聊天记忆初始化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个顶尖的自动控制原理考研导师。回答概念时，必须严谨、通俗，使用考研的标准术语。如果用户给出传递函数要求分析性能指标，你必须调用 analyze_system 工具进行计算。如果用户要求画图，请输出 MATLAB 代码。绝对不要废话。"}
    ]

# 6. 渲染历史对话
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 7. 接收用户输入
if prompt := st.chat_input("请输入你的自控问题（例如：帮我计算 G(s) = 10 / (s^2 + 2s + 10) 的超调量）"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("导师正在思考并计算..."):
            try:
                # 第一次调用：判断是否需要用工具
                response = client.chat.completions.create(
                    model="glm-4-air",
                    messages=st.session_state.messages,
                    tools=tools_definition,
                    tool_choice="auto"
                )
                response_message = response.choices[0].message
                
                if response_message.tool_calls:
                    st.info("🔧 检测到数学计算需求，正在调用 Python 控制库计算...")
                    
                    tool_call = response_message.tool_calls[0]
                    args = json.loads(tool_call.function.arguments)
                    
                    # 运行工具计算
                    tool_result = analyze_system(args.get("num"), args.get("den"))
                    
                    st.session_state.messages.append(response_message.model_dump())
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                    
                    # 第二次调用：根据计算结果给出最终回答
                    final_response = client.chat.completions.create(
                        model="glm-4-air",
                        messages=st.session_state.messages
                    )
                    final_reply = final_response.choices[0].message.content
                else:
                    final_reply = response_message.content
                
                st.markdown(final_reply)
                st.session_state.messages.append({"role": "assistant", "content": final_reply})

                # 自动识别并画图
                # 自动识别并画图
                if "超调量" in final_reply or "调节时间" in final_reply:
                    st.info("📈 导师正在为您绘制阶跃响应曲线...")
                    fig = plot_system([10], [1, 2, 10], plot_type="step")
                    if fig:
                        st.pyplot(fig)

                elif "根轨迹" in final_reply:
                    st.info("📈 导师正在为您绘制根轨迹图...")
                    # 注意：这里传入的是它推导出的开环传递函数分母 [1, 2, 0]
                    fig = plot_system([10], [1, 2, 0], plot_type="root")
                    if fig:
                        st.pyplot(fig)
            except Exception as e:
                st.error(f"出错了：{e}")
