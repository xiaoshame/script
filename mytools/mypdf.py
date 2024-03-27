from PyPDF2 import PdfReader, PdfWriter
# from fpdf import FPDF
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

def merge_pdf(input_file_list,output_file_path):

    # 创建PDF写入器对象
    writer = PdfWriter()

    # 遍历列表，逐个打开PDF文件
    for pdf in input_file_list:
        reader = PdfReader(pdf)
        # 将每页添加到写入器对象中
        for page in reader.pages:
            writer.add_page(page)

    # 写入合并后的PDF文件
    with open(output_file_path, "wb") as f_out:
        writer.write(f_out)

    print("PDF文件合并完成。")


def image_to_pdf(image_input_list, pdf_path):

    # 定义A4纸大小
    a4_width, a4_height = A4

    for image_path in image_input_list:
            # 创建一个PDF画布
        c = canvas.Canvas(pdf_path + "\\" + os.path.splitext(os.path.basename(image_path))[0] + ".pdf")
        # 使用PIL打开图片以获取尺寸信息
        with Image.open(image_path) as img:
            img_width, img_height = img.size
            # 计算缩放比例
            scale = min(a4_width / img_width, a4_height / img_height)
            # 应用缩放比例
            scaled_width, scaled_height = img_width * scale, img_height * scale
            # 居中显示
            x = (a4_width - scaled_width) / 2
            y = (a4_height - scaled_height) / 2
            # 将调整后的图片绘制到PDF上
            c.drawImage(image_path, x, y, width=scaled_width, height=scaled_height)
        # 保存PDF
        c.save()
        print(image_path + "转换PDF完成。")

# def image_to_pdf(image_input_list, pdf_path):
#     # 遍历列表，逐个打开PDF文件
#     for image_path in image_input_list:
#         image = Image.open(image_path)
#         # 如果图片不是RGB模式，转换之
#         if image.mode != 'RGB':
#             image = image.convert('RGB')
#         image.save(pdf_path + "\\" + os.path.splitext(os.path.basename(image_path))[0] + ".pdf", "PDF", resolution=100.0)
#         print(image_path + "转换PDF完成。")