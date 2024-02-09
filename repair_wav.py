import os
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
target_dir = 'problem'
repair_dir = 'repair'
os.makedirs(target_dir, exist_ok=True)
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
        target_file = os.path.join(target_dir, base_name)
        repair_file = os.path.join(repair_dir, base_name)
        shutil.copy(wav_path, target_file)
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
