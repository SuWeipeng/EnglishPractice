# 输入文件名
fileName       = "IELTS1000"

from modules.FileRead import FileRead

vocabulary = ["IELTS1000"]
def main():
    if fileName in vocabulary:
        fr = FileRead(fileName)
        fr.readContentToDB()
    
if __name__ == '__main__':
    main()