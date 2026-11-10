import streamlit as st
import os
import re
import base64
from dotenv import load_dotenv
from openai import OpenAI
from tools import calculate_routh, analyze_system, plot_system

# 1. 网页基础设置
st.set_page_config(page_title="自控原理导师", page_icon="📈", layout="wide")
st.title("📈 自动控制原理 AI 导师")
st.caption("内置多格式文件解析、高精度计算引擎与AI联动")

with st.sidebar:
    st.header("⚙️ 控制面板")
    if st.button("🗑️ 清空对话记忆"):
        st.session_state.messages = []
        st.rerun()

# 2. 初始化 API (注意：请确保你的智谱 API Key 有 glm-4v 权限)
load_dotenv()
API_KEY = os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4")

# ==========================================
# 【核心区 1】：多格式文件解析与图片识别
# ==========================================
st.subheader("📂 自动批改与解题系统（支持 TXT / DOCX / PDF / 图片）")

uploaded_file = st.file_uploader("上传题目文件或截图", type=["txt", "docx", "pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_name = uploaded_file.name
    ext = file_name.split(".")[-1].lower()
    file_content = ""
    
    if ext == "txt":
        file_content = uploaded_file.read().decode("utf-8")
        st.info(f"📄 已成功读取 TXT 文件内容：\n{file_content[:100]}...")
        
    elif ext == "docx":
        import docx
        doc = docx.Document(uploaded_file)
        file_content = "\n".join([para.text for para in doc.paragraphs])
        st.info(f"📄 已成功读取 Word 文件内容：\n{file_content[:100]}...")
        
    elif ext == "pdf":
        import pypdf
        reader = pypdf.PdfReader(uploaded_file)
        for page in reader.pages:
            file_content += page.extract_text() + "\n"
        st.info(f"📄 已成功读取 PDF 文件内容：\n{file_content[:100]}...")
        
    elif ext in ["png", "jpg", "jpeg"]:
        st.info("🖼️ 检测到图片，将调用多模态视觉模型进行识别...")

    if st.button("一键解题"):
        # 处理图片逻辑
        if ext in ["png", "jpg", "jpeg"]:
            img_data = uploaded_file.read()
            base64_image = base64.b64encode(img_data).decode('utf-8')
            
            st.info("AI 正在通过视觉模型看题...")
            try:
                vision_response = client.chat.completions.create(
                    model="glm-4v", 
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "请仔细阅读图片。如果图片是特征方程，请只输出系数（用逗号隔开，不要写其他字）；如果图片是其他自控题目，请直接解答这道题。"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ]
                )
                answer = vision_response.choices[0].message.content
                
                # 判断提取的是不是纯数字
                if all(c in "0123456789,.- " for c in answer.strip()):
                    st.success(f"识别到特征方程系数：{answer}。正在硬核计算...")
                    nums = [float(x.strip()) for x in answer.replace("，", ",").split(",")]
                    res = calculate_routh(nums)
                    st.code(res)
                    st.session_state.last_result = res
                else:
                    st.markdown(answer)
                    st.session_state.last_result = "用户上传了一张图片，AI 已经进行了解答。"
            except Exception as e:
                st.error(f"图片识别失败: {e}")
                
        # 处理文字文档逻辑
        else:
            clean_text = file_content.replace(" ", "")
            eq_part = clean_text.split("=")[1] if "=" in clean_text else clean_text
            eq_part_clean = re.sub(r's\^\d+|s', '', eq_part)
            all_nums = [float(x) for x in re.findall(r'[+-]?\d+\.?\d*', eq_part_clean)]
            
            if len(all_nums) >= 4:
                nums = all_nums[:5]
                if len(nums) == 4:
                    nums.insert(0, 1.0)
            else:
                nums = []
                
            if nums:
                st.success(f"提取到的系数为：{nums}。正在计算...")
                res = calculate_routh(nums)
                st.code(res)
                st.session_state.last_result = res
            else:
                st.error("无法从文件中提取到有效的数字系数。")

st.divider()

# ==========================================
# 【核心区 2】：手动高精度计算站
# ==========================================
st.subheader("🧮 自控原理高精度计算站")
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
                nums = [float(x.strip()) for x in coeffs.replace("，", ",").split(",")]
                res = calculate_routh(nums)
                st.success("计算完成：")
                st.code(res)
                st.session_state.last_result = res
            except Exception as e:
                st.error(f"输入有误: {e}")
    
    elif calc_type == "系统性能指标计算（超调量/调节时间）":
        st.write("请输入系统的传递函数分子和分母系数")
        col1, col2 = st.columns(2)
        with col1:
            num_str = st.text_input("分子系数（num）：", value="10")
        with col2:
            den_str = st.text_input("分母系数（den）：", value="1, 2, 10")
            
        if st.button("开始计算性能指标"):
            if num_str and den_str:
                try:
                    num = [float(x.strip()) for x in num_str.replace("，", ",").split(",")]
                    den = [float(x.strip()) for x in den_str.replace("，", ",").split(",")]
                    res = analyze_system(num, den)
                    st.success("计算完成：")
                    st.code(res)
                    
                    fig = plot_system(num, den, plot_type="step")
                    if fig:
                        st.pyplot(fig)
                    st.session_state.last_result = f"性能指标计算结果：\n{res}"
                except Exception as e:
                    st.error(f"输入有误: {e}")
        
    st.divider()
    
    # ==========================================
    # 【核心区 3】：AI 导师聊天区（带上下文联动）
    # ==========================================
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "你是一个资深的自动控制原理导师。如果用户带来了计算器的结果让你解释，请结合数据进行分析。绝对不要说你没看到结果。"}
        ]
        
    for msg in st.session_state.messages:
        if msg["role"] in ["user", "assistant"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
    if prompt := st.chat_input("在这里问概念（例如：上面的劳斯表稳定吗？）"):
        with st.chat_message("user"):
            st.markdown(prompt)
        
    context_text = ""
    if "last_result" in st.session_state and st.session_state.last_result:
        context_text = f"【系统强制提示：请结合上方计算器刚刚算出的结果来回答用户，结果如下：\n{st.session_state.last_result}】\n\n"
    
    enhanced_prompt = context_text + f"用户问题：{prompt}"
    st.session_state.messages.append({"role": "user", "content": enhanced_prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("导师正在结合上方数据思考..."):
            try:
                response = client.chat.completions.create(
                    model="glm-4-plus",
                    messages=st.session_state.messages
                )
                reply = response.choices[0].message.content
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"出错了：{e}")
