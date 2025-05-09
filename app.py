# app.py

from flask import Flask, render_template, request
import random
import math # 新增：引入 math 模块用于计算距离

app = Flask(__name__)

# --- 数据定义 ---
PALACE_ORDER = ["大安", "留连", "速喜", "赤口", "小吉", "空亡"]

# 宫位与**标准颜色名称**的映射 (保持不变，用于逻辑清晰)
PALACE_COLORS_MAPPING = {
    "大安": "青绿",
    "留连": "黄棕",
    "速喜": "红",
    "赤口": "白金",
    "小吉": "黑蓝",
    "空亡": "黄白"
}

# 特殊结果的含义（没穿内裤或内裤破损）
SPECIAL_OUTCOME_MEANINGS = {
    "去口": "没穿内裤或内裤破损",
    "空王": "没穿内裤或内裤破损"
}

# 宫位名称对应的十六进制颜色值，用于混合计算
PALACE_COLORS_HEX_MAPPING = {
    "青绿": "#008080",  # Teal (青绿色)
    "黄棕": "#A0522D",  # Sienna (黄褐色，接近文档描述的黄棕)
    "红": "#FF0000",   # Red (纯红色)
    "白金": "#E5E4E2",  # Platinum (白金色，接近浅灰色)
    "黑蓝": "#000080",  # Navy (海军蓝，深蓝色，接近黑蓝色)
    "黄白": "#FFFFE0"   # Light Yellow (浅黄色，接近黄白色)
}

# 新增：一个包含常见中文颜色名称和对应十六进制值的字典
# 这个列表可以根据需要扩展，以获得更详细或更多样化的颜色名称
NAMED_COLORS_HEX = {
    "纯白": "#FFFFFF", "雪白": "#FFFAFA", "象牙白": "#FFFFF0",
    "浅灰": "#D3D3D3", "银灰": "#C0C0C0", "中灰": "#808080", "深灰": "#A9A9A9", "黑": "#000000",

    "亮红": "#FF0000", "鲜红": "#FF4444", "深红": "#8B0000", "玫瑰红": "#FF007F", "酒红": "#800000", "番茄红": "#FF6347",

    "亮绿": "#00FF00", "草绿": "#7CFC00", "深绿": "#006400", "翠绿": "#00A000", "橄榄绿": "#808000", "森林绿": "#228B22",

    "亮蓝": "#0000FF", "天蓝": "#87CEEB", "海军蓝": "#000080", "宝蓝": "#4169E1", "深蓝": "#0000CD", "靛蓝": "#4B0082", "湖蓝": "#ADD8E6",

    "亮黄": "#FFFF00", "柠檬黄": "#FFFACD", "金黄": "#FFD700", "米黄": "#FFF8DC", "土黄": "#C3B04F",

    "橙": "#FFA500", "橘红": "#FF4500", "深橙": "#FF8C00",

    "紫": "#800080", "浅紫": "#D8BFD8", "深紫": "#4B0082", "薰衣草紫": "#E6E6FA", "紫罗兰": "#EE82EE",

    "粉": "#FFC0CB", "浅粉": "#FFB6C1", "深粉": "#FF1493",

    "棕": "#A52A2A", "巧克力棕": "#D2691E", "咖啡棕": "#6F4E37", "土棕": "#8B4513",

    "青": "#00FFFF", "青绿": "#008080", "水鸭绿": "#008B8B",

    "金": "#FFD700", "银": "#C0C0C0", "铜": "#B87333"
}


# --- 颜色转换辅助函数 ---
def hex_to_rgb(hex_color):
    """将十六进制颜色字符串转换为 RGB 元组 (R, G, B)。"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_color):
    """将 RGB 元组转换为十六进制颜色字符串。"""
    return '#%02x%02x%02x' % rgb_color

def calculate_color_distance(rgb1, rgb2):
    """计算两个 RGB 颜色之间的欧几里得距离（用于颜色相似度比较）。"""
    return math.sqrt(
        (rgb1[0] - rgb2[0])**2 +
        (rgb1[1] - rgb2[1])**2 +
        (rgb1[2] - rgb2[2])**2
    )

def get_approx_color_name(hex_color):
    """
    根据给定的十六进制颜色，从预定义的颜色名称列表中找到最接近的颜色名称。
    """
    if not isinstance(hex_color, str) or not hex_color.startswith('#'):
        return hex_color # 如果不是十六进制颜色字符串，直接返回原值

    target_rgb = hex_to_rgb(hex_color)
    min_distance = float('inf')
    closest_name = "未知颜色" # 默认值

    for name, hex_value in NAMED_COLORS_HEX.items():
        named_rgb = hex_to_rgb(hex_value)
        distance = calculate_color_distance(target_rgb, named_rgb)
        if distance < min_distance:
            min_distance = distance
            closest_name = name
    return closest_name


# --- 修改：核心混合颜色逻辑函数 ---
def get_combined_color(palace1_info, palace2_info, palace3_info, final_palace_is_special):
    """
    根据三个宫位的信息计算最终的“组合颜色”。
    使用 RGB 平均混合来模拟调色盘效果，并返回十六进制颜色代码。
    """
    # 如果第三个宫位是特殊情况，则直接返回其含义（文字）
    if final_palace_is_special:
        return palace3_info["color"] # 例如：“没穿内裤或内裤破损”

    # 获取三个宫位的名称
    name1 = palace1_info["name"]
    name2 = palace2_info["name"]
    name3 = palace3_info["name"]

    # 移除特殊标记，以获取实际宫位名称的颜色（处理 "空亡 (特殊)" 的情况）
    actual_name3 = name3.replace(" (特殊)", "")

    # 获取三个宫位对应的十六进制颜色代码
    color1_hex = PALACE_COLORS_HEX_MAPPING[PALACE_COLORS_MAPPING[name1]]
    color2_hex = PALACE_COLORS_HEX_MAPPING[PALACE_COLORS_MAPPING[name2]]
    color3_hex = PALACE_COLORS_HEX_MAPPING[PALACE_COLORS_MAPPING[actual_name3]]

    # 将十六进制转换为 RGB
    rgb1 = hex_to_rgb(color1_hex)
    rgb2 = hex_to_rgb(color2_hex)
    rgb3 = hex_to_rgb(color3_hex)

    # 计算 RGB 通道的平均值
    avg_r = int((rgb1[0] + rgb2[0] + rgb3[0]) / 3)
    avg_g = int((rgb1[1] + rgb2[1] + rgb3[1]) / 3)
    avg_b = int((rgb1[2] + rgb2[2] + rgb3[2]) / 3)

    # 将平均后的 RGB 转换回十六进制颜色代码
    return rgb_to_hex((avg_r, avg_g, avg_b))


# --- 核心预测逻辑函数（保持不变） ---
def calculate_prediction(dice1, dice2, dice3):
    palaces_calculated = []
    final_palace_is_special = False

    start_index = PALACE_ORDER.index("大安")
    palace1_index = (start_index + dice1 - 1) % len(PALACE_ORDER)
    palace1_name = PALACE_ORDER[palace1_index]
    palaces_calculated.append({"name": palace1_name, "color": PALACE_COLORS_MAPPING[palace1_name]})

    start_index = PALACE_ORDER.index(palace1_name)
    palace2_index = (start_index + dice2 - 1) % len(PALACE_ORDER)
    palace2_name = PALACE_ORDER[palace2_index]
    palaces_calculated.append({"name": palace2_name, "color": PALACE_COLORS_MAPPING[palace2_name]})

    palace3_name = ""
    palace3_meaning = ""

    if dice3 == 5:
        palace3_name = "空亡 (特殊)"
        palace3_meaning = SPECIAL_OUTCOME_MEANINGS["空王"]
        final_palace_is_special = True
    elif dice3 == 6:
        palace3_name = "去口"
        palace3_meaning = SPECIAL_OUTCOME_MEANINGS["去口"]
        final_palace_is_special = True
    else:
        start_index = PALACE_ORDER.index(palace2_name)
        palace3_index = (start_index + dice3 - 1) % len(PALACE_ORDER)
        palace3_name = PALACE_ORDER[palace3_index]
        palace3_meaning = PALACE_COLORS_MAPPING[palace3_name]

    palaces_calculated.append({"name": palace3_name, "color": palace3_meaning})

    final_predicted_color_hex_or_text = get_combined_color(
        palaces_calculated[0],
        palaces_calculated[1],
        palaces_calculated[2],
        final_palace_is_special
    )

    # 新增逻辑：根据最终颜色判断其名称，并传递给模板
    final_color_name = ""
    if isinstance(final_predicted_color_hex_or_text, str) and final_predicted_color_hex_or_text.startswith('#'):
        # 如果是十六进制颜色代码，则尝试获取其近似名称
        final_color_name = get_approx_color_name(final_predicted_color_hex_or_text)
    else:
        # 如果是特殊文本（例如“没穿内裤或内裤破损”），则直接用作名称
        final_color_name = final_predicted_color_hex_or_text


    return palaces_calculated, final_predicted_color_hex_or_text, final_color_name


# --- Flask 路由 ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        dice1 = int(request.form['dice1'])
        dice2 = int(request.form['dice2'])
        dice3 = int(request.form['dice3'])
    except (KeyError, ValueError):
        return "无效的骰子数字", 400

    palaces_calculated, final_predicted_color_hex_or_text, final_color_name = calculate_prediction(dice1, dice2, dice3)

    return render_template('result.html',
                           palaces=palaces_calculated,
                           final_color=final_predicted_color_hex_or_text, # 传递十六进制代码或特殊文本
                           final_color_name=final_color_name, # 传递近似颜色名或特殊文本
                           dice_rolls=[dice1, dice2, dice3])

# --- 运行应用 ---
if __name__ == '__main__':
    app.run(debug=True)