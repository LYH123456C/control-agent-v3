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
            # 1. 清洗并提取等号后面的部分
            clean_prompt = prompt.replace(" ", "")
            eq_part = clean_prompt.split("=")[1] if "=" in clean_prompt else clean_prompt
            
            # 2. 找到最高次幂
            max_power = 0
            power_matches = re.findall(r's\^(\d+)|s\b', eq_part)
            for p in power_matches:
                if p: # 如果是 s^5 这种
                    max_power = max(max_power, int(p))
                else: # 如果是单独的 s
                    max_power = max(max_power, 1)
            
            # 3. 按照最高次幂，初始化全 0 的系数列表
            nums = [0.0] * (max_power + 1)
            
            # 4. 挨个把项揪出来（支持正负号、小数）
            # 比如匹配 +3s^3，或者 -2s，或者 5
            terms = re.findall(r'([+-]?\d*\.?\d*)s\^(\d+)|([+-]?\d*\.?\d*)s\b|([+-]?\d+\.?\d*)$', eq_part)
            
            # 重新用更简单的方式解析（避免正则过于复杂）
            # 先把所有的 s^n 替换成特定的标记，方便提取
            # 这里用最暴力的替换法：
            temp_eq = eq_part
            
            # 找带 s 的项
            for match in re.finditer(r'([+-]?\d*\.?\d*)s(?:\^(\d+))?', temp_eq):
                coef_str = match.group(1)
                power_str = match.group(2)
                
                # 确定系数
                if coef_str == '' or coef_str == '+':
                    coef = 1.0
                elif coef_str == '-':
                    coef = -1.0
                else:
                    coef = float(coef_str)
                    
                # 确定次幂
                power = int(power_str) if power_str else 1
                
                # 填入数组对应位置
                if power <= max_power:
                    nums[max_power - power] = coef
                    
            # 找常数项（最后那个不带 s 的数字）
            const_match = re.search(r'([+-]?\d+\.?\d*)$', temp_eq.replace("=0", ""))
            if const_match:
                nums[-1] = float(const_match.group(1))
            
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
