from gtts import gTTS
import os, re
from pydub import AudioSegment
from datetime import datetime
from AutoTranslator import AutoTranslator
import string

FileName = "Small_Part2"
input_f  = FileName + ".srt"
output_f = FileName + ".txt"

link_base  = ''
src_lang   = 'en'
to_lang    = 'zh-cn'
translator = AutoTranslator(who='googletrans',src_lang=src_lang,to_lang=to_lang)

sentences    = []
translations = []
links        = []
valid_links  = []

def is_english_line(line):
    # 定义允许的英文字符和一些基本标点符号
    allowed_chars = string.ascii_letters + string.digits + string.whitespace + ".!?,'\"-"

    # 检查每个字符是否都在允许的字符集中
    return all(char in allowed_chars for char in line)

def safe_translate(translator, sentence, max_attempts=3):
    attempt = 0
    while attempt < max_attempts:
        try:
            # 尝试执行翻译操作
            translation = translator.trans(sentence)
            return translation  # 如果成功，返回翻译结果
        except Exception as e:  # 捕获所有异常
            print(f"Attempt {attempt + 1} failed with error: {e}")
            attempt += 1  # 增加尝试次数

    # 如果所有尝试都失败了，可以选择抛出异常或返回一个错误信息
    #raise Exception(f"Failed to translate after {max_attempts} attempts")
    print("!!!!!!! " + sentence + " !!!!!!! " + " traslate faild.")

def get_start_time_s(text):
    res = 0
    start_times = re.findall(r'(\d{2}:\d{2}:\d{2})', text)
    for time_str in start_times:
        time_obj = datetime.strptime(time_str, "%H:%M:%S")
        total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
        res = total_seconds
        break
    return res

with open(input_f,"r",encoding='utf-8') as file:
    for i, line in enumerate(file):
        start_s = 0
        link = link_base
        if (i-1)%4 == 0 and i >= 1:
            start_s = get_start_time_s(line.strip())
            link = link_base+str(start_s)
            links.append(link)
            print(link)
        if (i-2)%4 == 0 and i >= 2:
            sentence = line.strip()
            if sentence not in sentences and len(sentence) > 0 and is_english_line(sentence):
                sentences.append(sentence)
                trans = safe_translate(translator, sentence)
                translations.append(trans)
                valid_links.append(links[-1])
                print(links[-1],sentence,trans)

with open(output_f,"w",encoding='utf-8') as file:
    for i in range(len(sentences)):
        file.write(valid_links[i]+"\n")
        file.write(sentences[i].strip()+"\n")
        file.write(translations[i].strip()+"\n")