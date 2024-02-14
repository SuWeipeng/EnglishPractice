# 输入文件名
fileName       = 'PHRASE'

from modules.FileRead import FileRead
import os, json

VocabularyList = []
ListeningList  = []
def loadMaterials():
    global VocabularyList
    global ListeningList
    global AutoList
    try:
        with open("config/materials.json","r",encoding='utf-8') as file:
            configDict = json.load(file)
            if len(configDict) > 0:
                VocabularyList = configDict.get("vocabulary")
                ListeningList  = configDict.get("listening")
    except (RuntimeError, IOError) as e:
        print(e)
        #out, err = self._proc.communicate()
        #raise IOError('Error saving animation to file (cause: {0}) '
        #          'Stdout: {1} StdError: {2}. It may help to re-run '
        #          'with --verbose-debug.'.format(e, out, err))

if os.path.exists("config/materials.json"):
    loadMaterials()

vocabulary = VocabularyList
listening  = ListeningList
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