import streamlit as st
import os
import re
import base64
from dotenv import load_dotenv
from openai import OpenAI
from tools import calculate_routh

st.set_page_config(page_title="自控导师", page_icon="📈", layout="wide")
st.title("📈 自动控制原理 AI 导师")
st.caption("支持 TXT / Word / PDF / 图片题目解析与高精度计算")

load_dotenv()
API_KEY = os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4")

# ==========================================
# 【核心区 1】：多格式文件解析与多模态识图
# ==========================================
st.subheader("📂 自动批改与解题系统")
uploaded_file = st.file_uploader("上传题目文件或截图", type=["txt", "docx", "pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    ext = uploaded_file.name.split(".")[-1].lower()
    file_content = ""
    
    # 如果是文档，先提取里面的文字
    if ext == "txt":
        file_content = uploaded_file.read().decode("utf-8")
    elif ext == "docx":
        import docx
        doc = docx.Document(uploaded_file)
        file_content = "\n".join([para.text for para in doc.paragraphs])
    elif ext == "pdf":
        import pypdf
        reader = pypdf.PdfReader(uploaded_file)
        for page in reader.pages:
            file_content += page.extract_text() + "\n"
            
    if st.button("开始解题"):
        with st.spinner("AI 导师正在审题..."):
            try:
                # 【如果是图片，走视觉大模型】
                if ext in ["png", "jpg", "jpeg"]:
                    img_data = uploaded_file.read()
                    base64_image = base64.b64encode(img_data).decode('utf-8')
                    
                    response = client.chat.completions.create(
                        model="glm-4v",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "你是用户的私人解题助手。如果是求特征方程，直接输出系数数字。如果用户没有要求详细推导，请直接给出结果。绝对不要说'同学们好'或者'我来给大家解题'之类的废话。"},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]
                            }
                        ]
                    )
                    answer = response.choices[0].message.content
                    
                    # 判断是纯数字（算劳斯表）还是文字（推导题）
                    if all(c in "0123456789,.- " for c in answer.strip()):
                        st.success(f"提取到方程系数：{answer}")
                        nums = [float(x.strip()) for x in answer.replace("，", ",").split(",")]
                        st.code(calculate_routh(nums))
                    else:
                        st.markdown("### 📝 导师解答：")
                        st.markdown(answer)
                
                # 【如果是文字文档，走文本大模型】
                else:
                    st.info(f"📄 已提取文本内容，正在解答...")
                    response = client.chat.completions.create(
                        model="glm-4-plus",
                        messages=[{"role": "user", "content": f"你是一个自控原理导师。请详细解答这道题目：\n{file_content}"}]
                    )
                    st.markdown("### 📝 导师解答：")
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
# 【核心区 3】：AI 导师聊天区
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": "你是用户的私人自控智能助手。你的回答风格完全取决于用户的指令：\n"
                       "1. 如果用户只问答案或语气简短（如'算一下'、'答案是多少'），请直接给出最终结论和极简的数据，绝对不要解释推导过程。\n"
                       "2. 如果用户使用了'详细讲'、'推导一下'、'为什么'等词语，请展现你强大的推导能力，给出详细的步骤。\n"
                       "3. 绝对禁止任何'大家好'、'今天我们来'之类的客套话。"
        }
    ]

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
