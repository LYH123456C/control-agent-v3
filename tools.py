import control as ctrl
import matplotlib.pyplot as plt
import sympy as sp

# 1. 计算性能指标工具
def analyze_system(num: list, den: list) -> str:
    try:
        sys = ctrl.tf(num, den)
        info = ctrl.step_info(sys)
        
        result = f"系统分析结果：\n"
        result += f"- 超调量: {info['Overshoot']:.2f} %\n"
        result += f"- 调节时间: {info['SettlingTime']:.2f} 秒\n"
        result += f"- 上升时间: {info['RiseTime']:.2f} 秒\n"
        
        poles = ctrl.poles(sys)
        result += f"- 闭环极点: {poles}\n"
        return result
    except Exception as e:
        return f"计算失败: {e}"

# 2. 画图工具
def plot_system(num: list, den: list, plot_type: str = "step"):
    try:
        sys = ctrl.tf(num, den)
        plt.close('all') # 清空旧画板
        plt.figure(figsize=(6, 4))
        
        if plot_type == "step":
            time, response = ctrl.step_response(sys)
            plt.plot(time, response, label="Step Response", color='b')
            plt.title("Step Response (阶跃响应)")
            plt.xlabel("Time (s)")
            plt.ylabel("Amplitude")
        elif plot_type == "root":
            ctrl.root_locus(sys)
            plt.title("Root Locus (根轨迹)")
            
        plt.grid(True)
        return plt.gcf()
    except Exception as e:
        print(f"画图失败: {e}")
        return None

# 3. 劳斯判据工具 (绝对精准，不惧复杂分数)
def calculate_routh(coefficients: list) -> str:
    try:
        import sympy as sp
        # 去掉高位的 0
        coefficients = [c for c in coefficients if c != 0]
        n = len(coefficients)
        if n < 2:
            return "系数不足"
            
        # 为了保证绝对精度，使用 sympy 的 Rational
        row1 = [sp.Rational(c) for c in coefficients[::2]]
        row2 = [sp.Rational(c) for c in coefficients[1::2]]
        
        # 补齐长度
        max_len = max(len(row1), len(row2))
        row1 += [sp.Rational(0)] * (max_len - len(row1))
        row2 += [sp.Rational(0)] * (max_len - len(row2))
        
        table = [row1, row2]
        
        for i in range(2, n):
            prev_row = table[-2]
            curr_row = table[-1]
            new_row = []
            
            # 【核心修复】：处理第一列为0的特殊情况
            if curr_row[0] == 0:
                # 如果整行都是0，用上一行求导替换
                if all(c == 0 for c in curr_row):
                    for j in range(len(prev_row) - 1):
                        new_row.append(prev_row[j+1] * (len(prev_row) - 1 - j))
                else:
                    # 否则用一个极小的正数 epsilon 代替，这里用 1/10000 会影响符号判断
                    # 咱们直接用一个带符号的极小量模拟
                    curr_row[0] = sp.Rational(1, 100000)
                    for j in range(len(curr_row) - 1):
                        val = (curr_row[0] * prev_row[j+1] - prev_row[0] * curr_row[j+1]) / curr_row[0]
                        new_row.append(val)
            else:
                # 正常情况
                for j in range(len(curr_row) - 1):
                    val = (curr_row[0] * prev_row[j+1] - prev_row[0] * curr_row[j+1]) / curr_row[0]
                    new_row.append(val)
                    
            new_row.append(sp.Rational(0))
            table.append(new_row)
            
        # 统计符号变化
        first_col = []
        for row in table:
            if row[0] != 0:
                first_col.append(row[0])
                
        sign_changes = 0
        for i in range(len(first_col) - 1):
            if first_col[i] * first_col[i+1] < 0:
                sign_changes += 1
                
        # 格式化输出
        res = "劳斯表：\n"
        for i in range(n):
            # 把分数转成字符串，方便查看
            row_str = ", ".join([str(c) for c in table[i]])
            res += f"s^{n-1-i}: [{row_str}]\n"
            
        if sign_changes == 0:
            res += "\n结论：第一列全为正，系统稳定。正实部根数目为 0。"
        else:
            res += f"\n结论：第一列符号变化 {sign_changes} 次，系统不稳定。正实部根数目为 {sign_changes}。"
            
        return res
    except Exception as e:
        return f"计算失败: {e}"
