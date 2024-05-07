import json
import os

import inquirer
import openai
import requests
import yaml
import dashscope
import random
from dotenv import load_dotenv
from inquirer import prompt
from http import HTTPStatus

# 用于存储满足条件的文件信息
todo_files = []

# 遍历目录和子目录下的所有.md文件
def traverse_directory(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                process_md_file(filepath)

# 处理单个.md文件
def process_md_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分离yaml front matter和markdown内容
    front_matter, markdown_content = separate_front_matter(content)
    
    if front_matter and 'summary' in front_matter and front_matter['summary'] == 'todo':
        todo_files.append({
            'file_path': filepath,
            'title': front_matter.get('title', 'No Title'),
            'content': markdown_content
        })

# 分离yaml front matter和markdown内容
def separate_front_matter(content):
    front_matter = {}
    markdown_content = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            front_matter = yaml.safe_load(parts[1])
            markdown_content = parts[2:]

    return front_matter, markdown_content[0]

# 交互式选择文件
def select_file():
    choices = [{'title': f"{file['title']}", 'path': file['file_path']} for file in todo_files]
    questions = [inquirer.Checkbox('selected_file', message='选择一个文件来修改summary字段:', choices=choices)]
    selected_file = prompt(questions)['selected_file']
    return selected_file

def update_summary(path:str,instr:str):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
        new_content = text.replace("summary : 'todo'","summary : '%s'" % instr)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        f.close()
        print('%s 已更新summary字段。' % path)

## OPENAI API
def open_ai_summary(prompt):
    try:
        # Get environment variables
        token = os.environ.get("OPENAI_API_KEY")
        openai.api_key = token
        openai.proxy = "http://127.0.0.1:1081"
        response =  openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "请你充当一名文字专家，总结文章的摘要。下面是具体要求：1.摘要一共两句话 2. 摘要总字数限制在100字以内。下文是文章的内容，请你总结它："},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        print("OpenAI Error:", e)
        return None

## 百度API
def baidu_ai_summary(text: str):
    load_dotenv()
    # Get environment variables
    token = os.getenv("bd_qianfan_token")
    headers = {
        "Content-Type": "application/json;"
    }
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + token
    response = requests.post(url, headers=headers, data=json.dumps({"messages": [{"role": "user", "content":"总结概述下面文章为一行内 100 汉字以内的一到三句话: " +  text}]}))
    obj = response.json()
    result = obj['result']
    usage_total_tokens = obj['usage']['total_tokens']
    print("Use {} tokens.".format(usage_total_tokens))
    return result

## 阿里API
def ali_ai_summary(title: str,text: str):
    messages = [
        {'role': 'user', 'content': "请你充当一名文字专家，对文章进行总结100字以内。下文是文章的标题：" + title + "下面是内容，请你总结它：" + text}]
    response = dashscope.Generation.call(
        'qwen1.5-72b-chat',
        messages=messages,
        # set the random seed, optional, default to 1234 if not set
        seed=random.randint(1, 10000),
        result_format='message',  # set the result to be "message" format.
    )
    if response.status_code != HTTPStatus.OK:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    result = response.output.choices[0]['message']['content']
    return result

# 主程序
if __name__ == '__main__':
    target_directory = 'D:/workspace/blog/content/posts'  # 修改为实际的目录路径
    traverse_directory(target_directory)

    for file in todo_files:
        # with open(file['file_path'], 'r', encoding='utf-8') as f:
        #     text = f.read()
        #     title, markdown_content = separate_front_matter(text)
        new_ai_summary = ali_ai_summary(file['title'],file['content'])
        print(new_ai_summary)
        update_summary(file['file_path'],new_ai_summary)

    print('替换完毕')