import wx
from PyPDF2 import PdfReader, PdfWriter
# from fpdf import FPDF
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os


class PdfPage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()
    def initUI(self):
        ### PDF页面
        # 创建垂直布局管理器
        self.pdf_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # 创建列表框用于显示文件
        self.file_listbox = wx.ListBox(self)
        # 创建选择按钮
        self.pdf_open_button = wx.Button(self, label='选择文件')
        # 创建合并按钮
        self.pdf_merge_button = wx.Button(self, label='合并')
        # 创建图片转PDF按钮
        self.image_to_pdf_button = wx.Button(self, label='图片转PDF')
        # 创建列表框用于显示文件
        self.pdf_output_text_ctrl = wx.TextCtrl(self)

        # 将组件添加到布局管理器
        self.pdf_sizer.Add(self.file_listbox, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        self.pdf_sizer.Add(self.pdf_open_button, flag=wx.ALL|wx.EXPAND, border=10)
        self.pdf_sizer.Add(self.pdf_merge_button, flag=wx.ALL|wx.EXPAND, border=10)
        self.pdf_sizer.Add(self.image_to_pdf_button, flag=wx.ALL|wx.EXPAND, border=10)
        self.pdf_sizer.Add(self.pdf_output_text_ctrl, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)

        self.pdf_open_button.Bind(wx.EVT_BUTTON, self.on_open_file)
        self.pdf_merge_button.Bind(wx.EVT_BUTTON, self.on_merge_file)
        self.image_to_pdf_button.Bind(wx.EVT_BUTTON, self.on_image_to_pdf)
        # 设置面板使用布局管理器
        self.SetSizer(self.pdf_sizer)

    def on_open_file(self, event):
        # 创建文件选择对话框
        with wx.FileDialog(self, "选择文件", wildcard="所有文件 (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_MULTIPLE) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # 用户取消操作
            # 获取选择的文件路径
            paths = fileDialog.GetPaths()
            # 更新列表框内容
            self.file_listbox.Set(paths)

    def on_merge_file(self, event):
        # 创建目录选择对话框
        with wx.DirDialog(self, "选择保存路径", style=wx.DD_DEFAULT_STYLE) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return     # 用户取消操作
            # 获取选择的目录
            path = dirDialog.GetPath()
            # 显示选择的目录在文本框中
            self.pdf_output_text_ctrl.SetValue(path + "\merge.pdf")
            merge_pdf(self.file_listbox.GetStrings(),path+"\merge.pdf")

    def on_image_to_pdf(self,event):
        # 创建目录选择对话框
        with wx.DirDialog(self, "选择保存路径", style=wx.DD_DEFAULT_STYLE) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return     # 用户取消操作
            # 获取选择的目录
            path = dirDialog.GetPath()
            # 显示选择的目录在文本框中
            self.pdf_output_text_ctrl.SetValue(path)
            image_to_pdf(self.file_listbox.GetStrings(),path)
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