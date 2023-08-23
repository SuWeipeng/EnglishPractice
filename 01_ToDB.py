# 输入文件名
fileName       = "IELTS1000"

from modules.FileRead import FileRead

vocabulary = ["IELTS1000"]
listening  = ["Coversation01"]
def main():
    file_type = None
    if fileName in vocabulary:
        file_type = 1
    elif fileName in listening:
        file_type = 2
    fr = FileRead(fileName, file_type)
    if fileName in vocabulary:
        fr.readContentToDB()
    elif fileName in listening:
        fr.listeningContentToDB()

    
if __name__ == '__main__':
    main()