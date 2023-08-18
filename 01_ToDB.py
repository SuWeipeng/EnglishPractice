# 输入文件名
fileName       = "vocabulary"
inputFileName  = fileName+".txt"

from modules.FileRead import FileRead

def main():
    if fileName == "vocabulary":
        fr = FileRead(inputFileName)
        fr.readContentToDB()
    
if __name__ == '__main__':
    main()