from gtts import gTTS
import os, re
from pydub import AudioSegment

FileName = "ORCHARD7"
wordFile = FileName + ".txt"

WORD_UK = True
WORD_US = True
WORD_CN = False
SENTENCE_UK = False
SENTENCE_US = False
TRANSLATION = False

CHECK_FILE  = False

US_FILTER   = True
UK_FILTER   = True

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

def gtts_wav(text,out_path,lang='en'):
    # 使用gTTS库获取发音
    tts = gTTS(text, lang=lang)

    # 保存为MP3文件
    mp3_fp = out_path+".mp3"
    tts.save(mp3_fp)

    # 读取MP3文件
    sound = AudioSegment.from_mp3(mp3_fp)

    # 保存为WAV文件
    wav_fp = out_path+".wav"
    sound.export(wav_fp, format="wav")

    # 清理MP3文件
    os.remove(mp3_fp)

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
                    gtts_wav(filename,file_path,'zh-cn')
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
                gtts_wav(filename,file_path,'zh-cn')
            wordCount += 1
            print("Processed %d words.\n"%(wordCount))
            continue
