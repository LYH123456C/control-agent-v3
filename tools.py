import control as ctrl
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

def analyze_system(num: list, den: list) -> str:
    """
    输入传递函数的分子和分母系数，自动计算系统的性能指标。
    """
    try:
        # 1. 创建传递函数
        sys = ctrl.tf(num, den)
        
        # 2. 计算阶跃响应性能指标
        info = ctrl.step_info(sys)
        
        # 3. 拼接结果
        result = f"系统分析结果：\n"
        result += f"上升时间 (RiseTime): {info['RiseTime']:.2f} 秒\n"
        result += f"调节时间 (SettlingTime): {info['SettlingTime']:.2f} 秒\n"
        result += f"超调量 (Overshoot): {info['Overshoot']:.2f} %\n"
        return result
    except Exception as e:
        return f"计算失败，请检查输入格式，错误信息：{e}"
    import matplotlib.pyplot as plt
import control as ctrl

def plot_system(num: list, den: list, plot_type: str = "step"):
    """
    根据传递函数生成图表
    """
    try:
        sys = ctrl.tf(num, den)
        plt.close('all')
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