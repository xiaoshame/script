from PyPDF2 import PdfReader, PdfWriter

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
