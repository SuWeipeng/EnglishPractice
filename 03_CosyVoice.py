import sys, re, os
sys.path.append('third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio

cosyvoice = CosyVoice('pretrained_models/CosyVoice-300M-SFT')

FileName = "IELTS1000"
wordFile = "EnglishFiles/" + FileName + ".txt"

WORD_UK = False
WORD_US = False
WORD_CN = True
SENTENCE_UK = False
SENTENCE_US = True
TRANSLATION = True

CHECK_FILE  = False

US_FILTER   = False
UK_FILTER   = False

def remove_spaces(text):
    return text.replace(' ', '')

def replace_ellipsis(text):
    # 使用正则表达式将 ... 替换为 "什么什么"
    return re.sub(r'\.{3}', '"什么什么"', text)

print(replace_ellipsis('证明...正常'))
def sanitize_filename(filename):
    sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
    return sanitized

def create_folder(folder_path):
    try:
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created.")
    except FileExistsError:
        print(f"Folder '{folder_path}' already exists.")

def check_file(file_path):
    file_path += ".wav"
    if os.path.exists(file_path) and not CHECK_FILE:
        print(f"File '{file_path}' already exists. Skipping...")
        return True
    else:
        return False

def split_by_cn(cn):
    res = []
    # 移除括号及其内部的内容
    t = re.sub(r'（[^）]*）', '', cn)
    # 使用正则表达式按中文逗号和分号分割
    l = re.split(r'[，；]', t)
    num_l = len(l)
    for r in range(num_l):
        res.append(l[r])
    return res
def split_by_space(mean):
    res = []
    l = mean.replace(';', ' ')
    l = l.split()
    if len(l) % 2 != 0 or len(l) == 0:
        print("There is something wrong in the meaning.")
    else:
        num_l = int(len(l) / 2)
        for r in range(num_l):
            p = r * 2
            cn = l[p+1]
            for cn_1 in split_by_cn(cn):
                m = l[p] + ' ' + cn_1
                res.append(cn_1)
    res = list(set(res))
    return res

def gtts_wav(text, out_path, lang='en-us'):
    output_path = out_path + ".wav"
    if lang == 'en-us' or lang == 'en-uk':
        for i, j in enumerate(cosyvoice.inference_sft(text, '英文女', stream=False, speed=0.95)):
            torchaudio.save(output_path.format(i), j['tts_speech'], cosyvoice.sample_rate)
    elif lang == 'zh-cn':
        for i, j in enumerate(cosyvoice.inference_sft(replace_ellipsis(text), '中文女', stream=False, speed=1.0)):
            torchaudio.save(output_path.format(i), j['tts_speech'], cosyvoice.sample_rate)
    elif lang == 'zh-cn-sentence':
        for i, j in enumerate(cosyvoice.inference_sft(remove_spaces(text), '英文男', stream=False, speed=1.25)):
            torchaudio.save(output_path.format(i), j['tts_speech'], cosyvoice.sample_rate)

# 创建一个空列表来存储单词
words_us = []
words_uk = []
if US_FILTER:
    # 使用with语句打开文件，确保文件最后会被正确关闭
    with open('filter_us.txt', 'r') as file:
        # 逐行读取文件
        for line in file:
            # 移除每行末尾的换行符并添加到列表中
            words_us.append(line.strip())
if UK_FILTER:
    # 使用with语句打开文件，确保文件最后会被正确关闭
    with open('filter_uk.txt', 'r') as file:
        # 逐行读取文件
        for line in file:
            # 移除每行末尾的换行符并添加到列表中
            words_uk.append(line.strip())

with open(wordFile,"r",encoding='utf-8') as file:
    wordCount       = 0
    create_folder(FileName+'/words_us')
    create_folder(FileName+'/sentences_us')
    create_folder(FileName+'/words_uk')
    create_folder(FileName+'/sentences_uk')
    create_folder(FileName+'/translations')
    create_folder(FileName+'/words_cn')
    for i, line in enumerate(file):
        if i % 5 == 0 and not CHECK_FILE:
            filename = line.strip()
            clean_filename = sanitize_filename(filename)
            file_us_path=FileName+'/words_us/'+clean_filename
            file_uk_path=FileName+'/words_uk/'+clean_filename
            if WORD_US and not check_file(file_us_path):
                if US_FILTER and filename in words_us:
                    gtts_wav(filename,file_us_path,'en-us')
                elif not US_FILTER:
                    gtts_wav(filename,file_us_path,'en-us')
            if WORD_UK and not check_file(file_uk_path):
                if UK_FILTER and filename in words_uk:
                    gtts_wav(filename,file_uk_path,'en-uk')
                elif not US_FILTER:
                    gtts_wav(filename,file_uk_path,'en-uk')
        elif i % 5 == 1:
            continue
        elif i % 5 == 2:
            means = split_by_space(line.strip())
            for mean in means:
                file_path=FileName+'/words_cn/'+mean
                if WORD_CN and not check_file(file_path) and not CHECK_FILE:
                    gtts_wav(mean,file_path,'zh-cn')
        elif i % 5 == 3 and not CHECK_FILE:
            filename = line.strip()
            clean_filename = sanitize_filename(filename)
            file_path=FileName+'/sentences_us/'+clean_filename
            if SENTENCE_US and not check_file(file_path):
                gtts_wav(filename,file_path,'en-us')
            file_path=FileName+'/sentences_uk/'+clean_filename
            if SENTENCE_UK and not check_file(file_path):
                gtts_wav(filename,file_path,'en-uk')
        elif i % 5 == 4 and not CHECK_FILE:
            filename = line.strip()
            clean_filename = sanitize_filename(filename)
            file_path=FileName+'/translations/'+clean_filename
            if TRANSLATION and not check_file(file_path):
                gtts_wav(filename,file_path,'zh-cn-sentence')
            wordCount += 1
            print("Processed %d words.\n"%(wordCount))
            continue
