import os
import shutil

# 获取当前Python脚本所在的文件夹作为源文件夹
source_folder = os.path.dirname(os.path.abspath(__file__))

# 在当前脚本文件夹下创建一个名为'filter'的目标文件夹
filter_folder = os.path.join(source_folder, 'filter')

# 确保目标文件夹存在
if not os.path.exists(filter_folder):
    os.makedirs(filter_folder)

# 从当前目录下的filter.txt文件中读取要过滤的单词列表
words_to_filter = []
with open(os.path.join(source_folder, 'filter.txt'), 'r') as file:
    for line in file:
        # 移除每行的空白符并添加到列表
        words_to_filter.append(line.strip())

# 遍历源文件夹中的文件
for file in os.listdir(source_folder):
    # 分离文件名和扩展名
    filename, file_extension = os.path.splitext(file)

    # 检查文件是否是wav文件并且文件名在我们的列表中
    if file_extension == '.wav' and filename in words_to_filter:
        # 构建源文件和目标文件的完整路径
        source_file = os.path.join(source_folder, file)
        destination_file = os.path.join(filter_folder, file)

        # 如果目标文件夹中已存在同名文件，则不移动文件
        if not os.path.exists(destination_file):
            # 移动文件
            shutil.move(source_file, destination_file)
            print(f"Moved: {file}")

repair_script_content = """import os
import shutil
import wave
from pydub import AudioSegment

# 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件所在目录
current_dir = os.path.dirname(current_file_path)

# 获取当前目录下的所有文件和目录条目
entries = os.listdir(current_dir)

# 确保目标文件夹存在，如果不存在，则创建
#target_dir = 'problem'
repair_dir = 'repair'
#os.makedirs(target_dir, exist_ok=True)
os.makedirs(repair_dir, exist_ok=True)

# 过滤出文件，排除目录
files = [entry for entry in entries if os.path.isfile(os.path.join(current_dir, entry)) and entry.endswith('.wav')]

def fun_play_wav(wav_path):
    try:
        # 打开WAV音频文件
        wf = wave.open(wav_path, 'rb')
    except wave.Error as e:
        print(f"文件 {file} 无法打开，可能是损坏或非WAV文件，原因：{e}")
        base_name = os.path.basename(file)
        #target_file = os.path.join(target_dir, base_name)
        repair_file = os.path.join(repair_dir, base_name)
        #shutil.copy(wav_path, target_file)
        # 尝试修复文件
        try:
            audio = AudioSegment.from_wav(wav_path)
            audio.export(repair_file, format="wav", codec="pcm_s16le")
            print(f"文件 {base_name} 已被转码并保存到 {repair_file}")
        except Exception as repair_error:
            print(f"尝试修复文件 {base_name} 时出现错误：{repair_error}")

for file in files:
    full_path = os.path.join(current_dir, file)
    fun_play_wav(full_path)
"""

# 在 filter 文件夹中创建 repair_wav.py 文件
repair_script_path = os.path.join(filter_folder, 'wav_filter.py')
with open(repair_script_path, 'w', encoding='utf-8') as script_file:
    script_file.write(repair_script_content)

print(f"'repair_wav.py' script has been created in {filter_folder}")
