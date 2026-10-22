import streamlit as st
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from tools import calculate_routh, analyze_system, plot_system

# 1. 网页基础设置
st.set_page_config(page_title="自控原理导师", page_icon="📈", layout="wide")
st.title("📈 自动控制原理 AI 导师")
st.caption("内置高精度劳斯表计算引擎与性能指标计算")

with st.sidebar:
    st.header("⚙️ 控制面板")
    if st.button("🗑️ 清空对话记忆"):
        st.session_state.messages = [{"role": "system", "content": "你是一个顶尖的自控导师。"}]
        st.rerun()

# 2. 初始化 API
load_dotenv()
API_KEY = os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4")

# 3. 聊天记忆初始化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个顶尖的自控导师。回答需严谨，使用 Markdown 格式。"}
    ]

for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 4. 核心逻辑区
if prompt := st.chat_input("输入题目或问题（例如：用劳斯判据判断 D(s)=s^4+3s^3+3s^2+2s+2=0）"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        # 【拦截器 1】：识别劳斯判据
        if any(word in prompt for word in ["劳斯", "Routh", "判断稳定性", "特征方程"]):
            st.info("🔧 检测到方程，正在强行提取系数并用 Python 计算...")
            
            # 暴力清洗公式
            clean_prompt = prompt.replace(" ", "")
            eq_part = clean_prompt.split("=")[1] if "=" in clean_prompt else clean_prompt
            
            # 把 s^4 这种项剔除，只留纯系数
            eq_part_clean = re.sub(r's\^\d+|s', '', eq_part)
            
            # 提取所有数字（支持正负号）
            all_nums = [float(x) for x in re.findall(r'[+-]?\d+\.?\d*', eq_part_clean)]
            
            # 提取结果组装：补全首位系数
            if len(all_nums) >= 4:
                nums = all_nums[:5]
                if len(nums) == 4:
                    nums.insert(0, 1.0)
            else:
                nums = []
            
            if nums:
                # 强制调用 Python 工具
                tool_result = calculate_routh(nums)
                st.success("Python 计算完成！以下是绝对精准结果：")
                st.code(tool_result)
                
                # 让大模型把结果整理成标准回答
                st.session_state.messages.append({"role": "user", "content": f"Python 算出的劳斯表结果如下，请直接输出这段文本，不要修改任何数字或排版：\n{tool_result}"})
                final_response = client.chat.completions.create(
                    model="glm-4-plus",
                    messages=st.session_state.messages
                )
                final_reply = final_response.choices[0].message.content
                st.markdown(final_reply)
                st.session_state.messages.append({"role": "assistant", "content": final_reply})
            else:
                st.error("提取系数失败，请确保输入的是标准多项式。")
        
        # 【拦截器 2】：识别性能指标计算（超调量等）
        elif any(word in prompt for word in ["超调量", "调节时间", "上升时间", "性能指标"]):
            st.info("🔧 检测到计算指标需求...")
            st.warning("目前此页面仅支持劳斯判据的自动拦截计算，计算超调量请在本地代码中调用 analyze_system。")
        
        # 【普通问答】
        else:
            response = client.chat.completions.create(
                model="glm-4-plus",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
