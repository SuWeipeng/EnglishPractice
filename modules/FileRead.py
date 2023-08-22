import os
import sys
sys.path.append('./modules')
from ToDB import ToDB

class FileRead:
    debugReading = False
    def __init__(self,input_file):
        # 文件输入相关变量
        self.tableName       = input_file
        self.input_file      = self.tableName + ".txt"
        self.fullPathOfInput = ""
        self.get_inputfile_fullpath()
        # 主体内容相关变量
        self.word                   = None
        self.pronunciation          = None
        self.partOfSpeechAndMeaning = None
        self.exampleSentence        = None
        self.sentenceTranslation    = None
        # 创建数据库对旬
        self.db = ToDB("English.db")
        self.db.createTable(self.tableName)
    def get_inputfile_fullpath(self):
        '''
        得到输入文件的完整路径，将之存入 self.fullPathOfInput 变量。
        '''
        for dirName, subdirList, fileList in os.walk(os.getcwd()):
            for fname in fileList:
                if fname == self.input_file:
                    self.fullPathOfInput = ('%s' % dirName+'\\'+fname)
    def readContentToDB(self,replace = False):
        '''
        readContent(True) 会对重复单词的内容进行替换。
        默认是 False, 会忽略重复内容。
        '''
        with open(self.fullPathOfInput,"r",encoding='utf-8') as file:
            for i, line in enumerate(file):
                # https://blog.csdn.net/editkiller/article/details/8500123
                # “I''m” 在数据库里存成 “I'm”，因此需替换 line 中的英文单引号。
                if "'" in line:
                    line = line.replace("'","''")
                if i % 5 == 0:
                    self.word = line.strip()
                    if self.debugReading:
                        print("word: " + self.word)
                elif i % 5 == 1:
                    self.pronunciation = line.strip()
                    if self.debugReading:
                        print("pronunciation: " + self.pronunciation)
                elif i % 5 == 2:
                    self.partOfSpeechAndMeaning = line.strip()
                    if self.debugReading:
                        print("part of speech and meaning: " + self.partOfSpeechAndMeaning)
                elif i % 5 == 3:
                    self.exampleSentence = line.strip()
                    if self.debugReading:
                        print("example sentence: " + self.exampleSentence)
                elif i % 5 == 4:
                    self.sentenceTranslation = line.strip()
                    if self.debugReading:
                        print("sentence translation: " + self.sentenceTranslation)
                    self.db.insertVocabulary(self.word,
                                             self.pronunciation,
                                             self.partOfSpeechAndMeaning,
                                             self.exampleSentence,
                                             self.sentenceTranslation,
                                             replace)
        self.db.to_disk()
    def dbg(self):
        '''
        打印一些用于 Debug 信息。
        '''
        print("self.fullPathOfInput is " + self.fullPathOfInput)
