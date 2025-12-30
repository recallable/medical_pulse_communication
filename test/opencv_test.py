import cv2
import pytesseract

# -------------------------- 第一步：配置Tesseract路径（仅Windows需要） --------------------------
# 如果是Windows系统，需指定Tesseract的安装路径；Linux/Mac无需这一步
pytesseract.pytesseract.tesseract_cmd = r'D:\exploitation\app\Tesseract-OCR\tesseract.exe'


# -------------------------- 第二步：定义图像预处理函数（OpenCV核心作用） --------------------------
def preprocess_image(image_path):
    """
    图像预处理：提升OCR识别准确率
    步骤：读取图像 → 灰度化 → 降噪 → 二值化 → （可选）形态学操作
    """
    # 1. 读取图像（BGR格式）
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图像：{image_path}")

    # 2. 转为灰度图像（减少颜色干扰，降低计算量）
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. 降噪（高斯模糊，去除图像噪点）
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # 4. 二值化（将图像转为黑白，突出文字轮廓）
    # 自适应二值化：适合光照不均匀的图像，参数可根据实际调整
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  # 自适应阈值方法
        cv2.THRESH_BINARY_INV,  # 二值化方式（反色，文字为白，背景为黑）
        11,  # 块大小（奇数）
        2  # 常数项
    )

    # 5. （可选）形态学操作：去除小噪点，优化文字边缘
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return processed, img


# -------------------------- 第三步：OCR识别主函数 --------------------------
def ocr_image(image_path, lang='eng'):
    """
    执行OCR识别
    :param image_path: 图像路径
    :param lang: 识别语言（eng=英文，chi_sim=简体中文，eng+chi_sim=中英混合）
    :return: 识别的文字结果
    """
    # 预处理图像
    processed_img, original_img = preprocess_image(image_path)

    # 调用Tesseract进行OCR识别
    # config参数：--psm 6 表示“假设图像是单一均匀的文本块”（最常用的模式）
    result = pytesseract.image_to_string(
        processed_img,
        lang=lang,
        config='--psm 6'
    )

    # （可选）显示预处理后的图像和原始图像（方便调试）
    cv2.imshow('Original Image', original_img)
    cv2.imshow('Processed Image', processed_img)
    cv2.waitKey(0)  # 按任意键关闭窗口
    cv2.destroyAllWindows()

    return result.strip()  # 去除结果中的空白字符


# -------------------------- 测试示例 --------------------------
if __name__ == "__main__":
    # 替换为你的图像路径（建议用清晰、文字端正的图像）
    image_path = r"C:\Users\31948\Desktop\OIP-C.webp"

    # 识别英文（lang='eng'），识别中文则改为lang='chi_sim'，中英混合用lang='eng+chi_sim'
    ocr_result = ocr_image(image_path, lang='chi_sim')

    print("OCR识别结果：")
    print(ocr_result)