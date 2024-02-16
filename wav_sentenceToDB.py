# 输入文件名
fileName       = 'sentences'

from modules.FileRead import FileRead
import os, json

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
                AutoList       = configDict.get("auto")
    except (RuntimeError, IOError) as e:
        print(e)
        #out, err = self._proc.communicate()
        #raise IOError('Error saving animation to file (cause: {0}) '
        #          'Stdout: {1} StdError: {2}. It may help to re-run '
        #          'with --verbose-debug.'.format(e, out, err))

if os.path.exists("config/materials.json"):
    loadMaterials()

auto  = AutoList
def main():
    fr = FileRead(fileName, 2)
    if fileName in auto:
        try:
            fr.deleteTable(fileName)
            fr.createTable(fileName)
        except:
            print("no sentences table.")
        fr.listeningContentToDB(True)

if __name__ == '__main__':
    main()