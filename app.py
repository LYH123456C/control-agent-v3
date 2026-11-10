import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from tools import calculate_routh,analyze_system,plot_system

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
# 【新增区】：文件上传与解析
# ==========================================
st.subheader("📂 自动批改与解题系统")
uploaded_file = st.file_uploader("上传你的题目文件（仅支持 .txt 格式）", type=["txt"])

if uploaded_file is not None:
    # 读取文件里的文字
    file_content = uploaded_file.read().decode("utf-8")
    st.info(f"📄 已成功读取文件，内容预览：\n{file_content[:100]}...")
    
    if st.button("一键解题"):
        # 这里用正则把文件里的数字全抠出来
        import re
        clean_text = file_content.replace(" ", "")
        eq_part = clean_text.split("=")[1] if "=" in clean_text else clean_text
        # 剔除 s^4 这种干扰项，只留系数
        eq_part_clean = re.sub(r's\^\d+|s', '', eq_part)
        all_nums = [float(x) for x in re.findall(r'[+-]?\d+\.?\d*', eq_part_clean)]
        
        # 补齐首项系数
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
            # 存入记忆，让下面的 AI 也能看到
            st.session_state.last_result = res
        else:
            st.error("无法从文件中提取到有效的数字系数，请检查文件内容格式。")

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
               # 先把中文逗号替换成英文，然后再按英文逗号切分并去掉空格
                nums = [float(x.strip()) for x in coeffs.replace("，", ",").split(",")]
                st.info("正在使用底层 Fraction 库进行绝对精准计算...")
                res = calculate_routh(nums)
                st.success("计算完成：")
                st.code(res)
                st.session_state.last_result = res
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
                num = [float(x.strip()) for x in num_str.replace("，", ",").split(",")]
                den = [float(x.strip()) for x in den_str.replace("，", ",").split(",")]
                st.info("正在调用 Python control 库计算...")
                res = analyze_system(num, den)
                st.success("计算完成：")
                st.code(res)
                
                # 顺便把图画出来
                fig = plot_system(num, den, plot_type="step")
                if fig:
                    st.pyplot(fig)
                    st.session_state.last_result = f"性能指标计算结果：\n{res}"
                    st.session_state.last_result = res + " (并画出了阶跃响应图)"
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
            st.session_state.last_result = res  # 存入长期记忆
        except Exception as e:
            st.error(f"输入有误: {e}")

st.divider()
# ==========================================

# 3. 聊天区
if "messages" not in st.session_state:
    # 解开死命令，让它允许结合数据进行解释
    st.session_state.messages = [{"role": "system", "content": "你是一个资深的自动控制原理导师。请解答概念问题。如果用户带来了计算器的结果让你解释，请结合数据进行分析。绝对不要说你没看到结果。"}]

# 渲染历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 接收输入（确保整个文件里只有这一个 st.chat_input）
if prompt := st.chat_input("在这里问概念（例如：上面的劳斯表稳定吗？）"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 【终极拦截】：强行把计算器的结果抓出来，贴在大模型脸上
    context_text = ""
    if "last_result" in st.session_state and st.session_state.last_result:
        context_text = f"【系统强制提示：请结合上方计算器刚刚算出的结果来回答用户，不要说你没看到！结果如下：\n{st.session_state.last_result}】\n\n"
    
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
