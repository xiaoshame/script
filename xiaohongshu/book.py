from bs4 import BeautifulSoup

# 读取HTML文件
with open('./xiaohongshu/1.html', 'r', encoding='utf-8') as file:
    html_doc = file.read()
# 创建BeautifulSoup对象
soup = BeautifulSoup(html_doc, 'html.parser')

# 提取段落内容
paragraph = soup.find_all('a', class_='one_book_info')
for parent in paragraph:
    title = parent.get('title')
    span_content = parent.find('div', class_='readed_count')
    text = span_content.find('span').text
    count = parent.find('div', class_='readed_age').text
    print(title + " " + text + " " + count)
