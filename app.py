import streamlit as st
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from tools import calculate_routh

# 1. 网页基础设置
st.set_page_config(page_title="自控原理导师", page_icon="📈", layout="wide")
st.title("📈 自动控制原理 AI 导师")
st.caption("内置高精度劳斯表计算引擎（基于 SymPy）")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 控制面板")
    if st.button("🗑️ 清空对话记忆"):
        st.session_state.messages = [{"role": "system", "content": "你是一个顶尖的自控导师。"}]
        st.rerun()

# 2. 初始化 API
load_dotenv()
API_KEY = os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4")

# 3. 核心功能区：直接输入系数，用 Python 算！
st.subheader("🧮 劳斯判据高精度计算器")
st.write("请输入特征方程的系数（降幂排列，用逗号隔开），例如：`1, 3, 3, 2, 2`")
coeff_input = st.text_input("特征方程系数：")

if st.button("开始硬核计算"):
    if coeff_input:
        try:
            # 把字符串转换成数字列表
            nums = [float(x.strip()) for x in coeff_input.split(",")]
            st.info("🔧 正在调用底层 SymPy 库进行绝对精准计算...")
            # 直接调用 tools.py 里的函数
            result_text = calculate_routh(nums)
            
            st.success("✅ 计算完成！以下为绝对精准结果：")
            st.text(result_text)
        except Exception as e:
            st.error(f"输入格式有误：{e}")
    else:
        st.warning("请先输入系数！")

st.divider()

# 4. 聊天区
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "你是一个顶尖的自控导师。请用通俗语言解释概念。"}]

for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("在这里问概念，例如：什么是超调量？"):
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
