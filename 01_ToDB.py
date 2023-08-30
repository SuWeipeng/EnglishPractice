# 输入文件名
fileName       = 'SenteceStructure01'

from modules.FileRead import FileRead

vocabulary = ['IELTS1000','ORCHARD7']
listening  = ['Coversation01','SenteceStructure01','EnglishNews001']
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