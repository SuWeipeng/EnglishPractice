# 输入文件名
fileName       = "In1"
inputFileName  = fileName+".txt"

from modules.FileRead import FileRead

def main():
    fr = FileRead(inputFileName)
    fr.readContentToDB()
    
if __name__ == '__main__':
    main()