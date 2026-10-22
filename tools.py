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
        plt.close('all')
        plt.figure(figsize=(6, 4))
        
        if plot_type == "step":
            time, response = ctrl.step_response(sys)
            plt.plot(time, response, label="Step Response", color='b')
            plt.title("Step Response ")
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

# 3. 劳斯判据工具 (重写后的硬核版)
def calculate_routh(coefficients: list) -> str:
    try:
        from fractions import Fraction
        # 清理前导0
        while len(coefficients) > 1 and coefficients[0] == 0:
            coefficients.pop(0)
            
        n = len(coefficients)
        if n < 2:
            return "系数不足"
            
        # 初始化第一行和第二行
        row1 = [Fraction(c) for c in coefficients[::2]]
        row2 = [Fraction(c) for c in coefficients[1::2]]
        
        # 补全列数
        cols = (n + 1) // 2
        row1 += [Fraction(0)] * (cols - len(row1))
        row2 += [Fraction(0)] * (cols - len(row2))
        
        table = [row1, row2]
        
        # 计算后续行
        for i in range(2, n):
            prev_row = table[-2]
            curr_row = table[-1]
            new_row = []
            
            # 处理首列为0的情况
            if curr_row[0] == 0:
                if all(c == 0 for c in curr_row):
                    for j in range(cols):
                        power = (n - 1) - (i - 2) - (j * 2) 
                        if power > 0:
                            new_row.append(prev_row[j] * power)
                        else:
                            new_row.append(Fraction(0))
                else:
                    curr_row[0] = Fraction(1, 1000000)
                    for j in range(cols - 1):
                        val = (curr_row[0] * prev_row[j+1] - prev_row[0] * curr_row[j+1]) / curr_row[0]
                        new_row.append(val)
            else:
                for j in range(cols - 1):
                    val = (curr_row[0] * prev_row[j+1] - prev_row[0] * curr_row[j+1]) / curr_row[0]
                    new_row.append(val)
                    
            new_row.append(Fraction(0))
            table.append(new_row)
            
        # 统计第一列的符号变化
        first_col = [row[0] for row in table if row[0] != 0]
        sign_changes = 0
        for i in range(len(first_col) - 1):
            if first_col[i] * first_col[i+1] < 0:
                sign_changes += 1
                
        # 组装输出结果
        res = "劳斯表：\n"
        for i in range(n):
            row_strs = []
            for c in table[i]:
                if c.denominator == 1:
                    row_strs.append(str(c.numerator))
                else:
                    row_strs.append(f"{c.numerator}/{c.denominator}")
            res += f"s^{n-1-i}: [{', '.join(row_strs)}]\n"
            
        if sign_changes == 0:
            res += "\n结论：第一列全为正，系统稳定。正实部根数目为 0。"
        else:
            res += f"\n结论：第一列符号变化 {sign_changes} 次，系统不稳定。正实部根数目为 {sign_changes}。"
            
        return res
    except Exception as e:
        return f"计算失败: {e}"
