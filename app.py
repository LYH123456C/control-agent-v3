import streamlit as st
import os
import re
import base64
from dotenv import load_dotenv
from openai import OpenAI
from tools import calculate_routh

st.set_page_config(page_title="自控导师", page_icon="📈", layout="wide")
st.title("📈 自动控制原理 AI 导师")

load_dotenv()
API_KEY = os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4")

# ==========================================
# 【核心区 1】：文件上传与多模态识图
# ==========================================
st.subheader("📂 上传题目（图片 / TXT）")
uploaded_file = st.file_uploader("上传题目截图或文字文件", type=["txt", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    ext = uploaded_file.name.split(".")[-1].lower()
    
    if st.button("开始解题"):
        with st.spinner("AI 导师正在审题..."):
            try:
                if ext in ["png", "jpg", "jpeg"]:
                    # 图片走视觉大模型
                    img_data = uploaded_file.read()
                    base64_image = base64.b64encode(img_data).decode('utf-8')
                    
                    response = client.chat.completions.create(
                        model="glm-4v", # 视觉大模型
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "你是一个自控原理导师。请解答图片中的题目。如果是求特征方程/判断稳定性，请只输出系数数字；如果是化简或推导题，请给出详细步骤。"},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]
                            }
                        ]
                    )
                    answer = response.choices[0].message.content
                    
                    # 如果是纯数字，顺手算个劳斯表
                    if all(c in "0123456789,.- " for c in answer.strip()):
                        st.success(f"提取到方程系数：{answer}")
                        nums = [float(x.strip()) for x in answer.replace("，", ",").split(",")]
                        st.code(calculate_routh(nums))
                    else:
                        # 如果是推导题，直接展示大模型解答
                        st.markdown("### 📝 导师解答：")
                        st.markdown(answer)
                        
                else:
                    # 文本文件
                    content = uploaded_file.read().decode("utf-8")
                    response = client.chat.completions.create(
                        model="glm-4-plus",
                        messages=[{"role": "user", "content": f"请解答这道自控题目：\n{content}"}]
                    )
                    st.markdown(response.choices[0].message.content)
                    
            except Exception as e:
                st.error(f"解答失败：{e}")

st.divider()

# ==========================================
# 【核心区 2】：高精度劳斯表计算器
# ==========================================
st.subheader("🧮 劳斯表高精度计算器")
coeffs = st.text_input("输入特征方程系数（用逗号隔开，例如：1, 2, 3, 4, 5）")
if st.button("计算劳斯表"):
    if coeffs:
        try:
            nums = [float(x.strip()) for x in coeffs.replace("，", ",").split(",")]
            res = calculate_routh(nums)
            st.code(res)
            st.session_state.last_result = res
        except Exception as e:
            st.error(f"输入有误: {e}")

st.divider()

# ==========================================
# 【核心区 3】：聊天区
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "你是一个自控导师，请解答概念问题。"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("在这里问问题..."):
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
