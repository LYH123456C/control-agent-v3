import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from tools import calculate_routh

# 1. 网页基础设置
st.set_page_config(page_title="自控原理导师", page_icon="📈", layout="wide")
st.title("📈 自动控制原理 AI 导师")
st.caption("内置高精度劳斯表计算引擎")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 控制面板")
    if st.button("🗑️ 清空对话记忆"):
        st.session_state.messages = []
        st.rerun()

# 2. 初始化 API
load_dotenv()
API_KEY = os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4")

# ==========================================
# 【核心区】：绝对安全的“硬核计算器”
# ==========================================
st.subheader("🧮 劳斯判据高精度计算器")
st.write("请手动输入特征方程的系数（用逗号隔开，不要写 s，例如：`1, 1, 3, 3, 2, 2`）")
coeffs = st.text_input("输入系数：")

if st.button("开始硬核计算"):
    if coeffs:
        try:
            nums = [float(x.strip()) for x in coeffs.split(",")]
            st.info("正在使用底层 SymPy 库进行绝对精准计算...")
            res = calculate_routh(nums)
            st.success("计算完成：")
            # 这里用 st.code 保证表格格式100%不乱
            st.code(res)
        except Exception as e:
            st.error(f"输入有误: {e}")

st.divider()
# ==========================================

# 3. 聊天区（只聊概念，不准算劳斯表）
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "你是一个自控导师。请解答概念问题。不要尝试做劳斯表计算。"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("在这里问概念（例如：什么是超调量？）"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
