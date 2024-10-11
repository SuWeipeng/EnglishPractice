import re, os
import requests

FileName = "ORCHARD3"
wordFile = "EnglishFiles/" + FileName + ".txt"

CHECK_FILE = False

urlPiper = "http://192.168.5.3:5000"

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

def generate_wav(textToSpeak, file_path):
    payload = {'text': textToSpeak}
    r = requests.get(urlPiper,params=payload)
    with open(file_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

with open(wordFile,"r",encoding='utf-8') as file:
    wordCount       = 0
    create_folder("wav/"+FileName+'/words_us')
    create_folder("wav/"+FileName+'/sentences_us')
    for i, line in enumerate(file):
        if i % 5 == 0 and not CHECK_FILE:
            filename = line.strip()
            clean_filename = sanitize_filename(filename)
            file_path="wav/"+FileName+'/words_us/'+clean_filename+'.wav'
            if not check_file(file_path):
                generate_wav(filename, file_path)
        elif i % 5 == 1:
            continue
        elif i % 5 == 2:
            continue
        elif i % 5 == 3 and not CHECK_FILE:
            filename = line.strip()
            clean_filename = sanitize_filename(filename)
            file_path="wav/"+FileName+'/sentences_us/'+clean_filename+'.wav'
            if not check_file(file_path):
                generate_wav(filename, file_path)
        elif i % 5 == 4 and not CHECK_FILE:
            wordCount += 1
            print("Processed %d words.\n"%(wordCount))
            continue
