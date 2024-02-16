import shutil, os, re

wordFile = "EnglishFiles/sentences.txt"

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

def clear_folder(folder):
    # 如果文件夹存在且非空，则清空文件夹内容
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'无法删除 {file_path}。原因: {e}')

uk_target = 'wav/sentences/listen_uk'
us_target = 'wav/sentences/listen_us'
trans_tar = 'wav/sentences/translations'
fromFolder    = ''
with open(wordFile,"r",encoding='utf-8') as file:
    wordCount       = 0
    create_folder(uk_target)
    create_folder(us_target)
    create_folder(trans_tar)
    clear_folder(uk_target)
    clear_folder(us_target)
    clear_folder(trans_tar)
    for i, line in enumerate(file):
        if i % 3 == 0:
            fromFolder = line.strip()
        elif i%3 == 1:
            # 将指定文件复制到目标文件夹
            shutil.copy('wav/'+fromFolder+'/listen_uk/'+sanitize_filename(line.strip())+'.wav', uk_target)
            shutil.copy('wav/'+fromFolder+'/listen_us/'+sanitize_filename(line.strip())+'.wav', us_target)
        elif i%3 == 2:
            # 将指定文件复制到目标文件夹
            shutil.copy('wav/'+fromFolder+'/translations/'+sanitize_filename(line.strip())+'.wav', trans_tar)
            wordCount += 1
            print("Processed %d sentences.\n"%(wordCount))

import wav_sentenceToDB
wav_sentenceToDB.main()