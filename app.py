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
st.subheader("🧮 劳斯判据高精度计算站")
# 创建一个下拉菜单，让用户选择算什么
calc_type = st.selectbox(
    "请选择要计算的内容：", 
    ["劳斯判据稳定性分析", "系统性能指标计算（超调量/调节时间）"]
)

if calc_type == "劳斯判据稳定性分析":
    st.write("请输入特征方程的系数（降幂排列，用逗号隔开），例如：`1, 2, 3, 4, 5`")
    coeffs = st.text_input("输入系数：", key="routh_input")
    
    if st.button("开始计算劳斯表"):
        if coeffs:
            try:
                nums = [float(x.strip()) for x in coeffs.split(",")]
                st.info("正在使用底层 Fraction 库进行绝对精准计算...")
                res = calculate_routh(nums)
                st.success("计算完成：")
                st.code(res)
            except Exception as e:
                st.error(f"输入有误: {e}")

elif calc_type == "系统性能指标计算（超调量/调节时间）":
    st.write("请输入闭环传递函数的分子和分母系数（例如：分子填 `10`，分母填 `1, 2, 10`）")
    col1, col2 = st.columns(2)
    with col1:
        num_str = st.text_input("分子系数（num）：", value="10")
    with col2:
        den_str = st.text_input("分母系数（den）：", value="1, 2, 10")
        
    if st.button("开始计算性能指标"):
        if num_str and den_str:
            try:
                num = [float(x.strip()) for x in num_str.split(",")]
                den = [float(x.strip()) for x in den_str.split(",")]
                st.info("正在调用 Python control 库计算...")
                res = analyze_system(num, den)
                st.success("计算完成：")
                st.code(res)
                
                # 顺便把图画出来
                fig = plot_system(num, den, plot_type="step")
                if fig:
                    st.pyplot(fig)
            except Exception as e:
                st.error(f"输入有误: {e}")
# ==========================================
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
