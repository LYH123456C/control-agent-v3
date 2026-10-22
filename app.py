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

if prompt := st.chat_input("输入题目或问题（例如：用劳斯判据判断 D(s)=s^4+3s^3+3s^2+2s+2=0）"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        # 【核心逻辑】：只要检测到“劳斯”或“稳定性”，直接拦截！
        if any(word in prompt for word in ["劳斯", "Routh", "判断稳定性", "特征方程"]):
            st.info("🔧 检测到方程，正在强行提取系数并用 Python 计算...")
            
            # 1. 用正则表达式抓数字，只抓 s^ 后面或者带加减号的系数
            import re
            # 这一步非常关键，匹配类似 1, 3, 3, 2, 2 这种系数
            # 规则：找等号后面的数字，忽略 s^4 里面的 4
            clean_prompt = prompt.replace(" ", "")
            # 提取所有的数字
            all_nums = re.findall(r'(?<![s\^])\b\d+\b', clean_prompt)
            nums = [float(x) for x in all_nums[-5:]] # 取最后 5 个数
            
            # 2. 自动补齐最高次项的 1（如果用户没写 s^4 前面那个 1）
            if len(nums) == 4:
                nums.insert(0, 1.0)
            
            # 3. 强行调用咱们的工具
            tool_result = calculate_routh(nums)
            
            st.success("Python 计算完成！结果如下：")
            st.code(tool_result) # 直接硬核输出，不经过大模型
            
            # 4. 让大模型基于这个绝对正确的结果，写一段解释文字
            st.session_state.messages.append({"role": "user", "content": f"根据这个结果，用文字给用户解释一下系统为什么稳定/不稳定：\n{tool_result}"})
            final_response = client.chat.completions.create(
                model="glm-4-plus",
                messages=st.session_state.messages
            )
            final_reply = final_response.choices[0].message.content
            st.markdown(final_reply)
            st.session_state.messages.append({"role": "assistant", "content": final_reply})
            
        # 如果是问概念，正常聊天
        else:
            response = client.chat.completions.create(
                model="glm-4-plus",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
