from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QTextCursor, QColor, QIcon
from PyQt5 import uic
from modules.ReadWordFromDB import ReadWordFromDB
from modules.WriteEbbinghausDB import WriteEbbinghausDB
from modules.ReadEbbinghausDB import ReadEbbinghausDB
from modules.Ebbinghaus import Ebbinghaus
import json

class EnglishPractice:
    '''
    01. 与 ui 相关的函数名以         ui_ 开头
    02. 与数据库相关的函数名以       db_  开头
    03. 与文件相关的函数名以         f_   开头
    04. 功能相关的函数名以           fun_ 开头
    05. 与 Ebbinghous 相关的函数名以 eb_  开头
    '''
    practiceModeList = ['new','review','ebbinghaus']
    vocabulary_list  = ['IELTS1000']
    listening_list   = ['Coversation01']
    def __init__(self):
        self.generateAllWords = False
        # 打开单词数据库
        self.db               = ReadWordFromDB("English.db",EnglishPractice.vocabulary_list[0],EnglishPractice.listening_list[0])
        self.dbTables         = self.db.getTables()
        self.wordTables       = list(set(self.dbTables).intersection(set(EnglishPractice.vocabulary_list)))
        self.listeningTables  = list(set(self.dbTables).intersection(set(EnglishPractice.listening_list)))
        # 单词相关变量
        self.words            = []
        self.ebWords          = []
        self.pronunciations   = {}
        self.meanings         = {}
        self.sentences        = {}
        self.translations     = {}
        self.useSentenceScore = False
        self.updateInReview   = False
        self.wordMode         = 1
        self.practiceMode     = EnglishPractice.practiceModeList[self.wordMode]
        self.wordsNum         = 10
        self.wordIndex        = 0
        self.words_p_lines    = ''
        self.p_list           = []
        self.writeEbbinghaus  = WriteEbbinghausDB("Ebbinghaus.db")
        self.ebdb             = ReadEbbinghausDB("Ebbinghaus.db")
        self.score            = 0
        self.ebbinghaus       = Ebbinghaus()
        self.sentenceCriteria = 0.9
        # 听力相关变量
        self.links                 = []
        self.listeningSentences    = []
        self.listeningTranslations = []
        self.listenIndex           = 0
        self.listenCount           = self.db.getListenContent()
        # 从 UI 定义中动态 创建一个相应的窗口对象
        self.ui = uic.loadUi("ui/EnglishPractice.ui")
        self.radioButtonChanged    =    False
        self.ui.pushButton_7.setVisible(False)
        self.ui.pushButton_8.setVisible(False)
        # 听力设置相关
        self.ui.label_10.setText(str(self.listenCount))
        # Settings 中的 Word 数据源选择
        self.ui.comboBox.addItems(self.wordTables)
        self.ui.comboBox.currentIndexChanged.connect(self.ui_wordSourceChanged)
        # Settings 中的 Listening 数据源选择
        self.ui.comboBox_2.addItems(self.listeningTables)
        # Settings 模式选择
        self.ui.radioButton.clicked.connect(self.ui_selectEbbinghaus)
        self.ui.radioButton_2.clicked.connect(self.ui_selectReview)
        self.ui.radioButton_3.clicked.connect(self.ui_selectNew)
        self.checkBoxInitiated = False
        self.ui.checkBox.toggled.connect(self.ui_sentenceMode)
        self.checkBox_2Initicated = False
        self.ui.checkBox_2.toggled.connect(self.ui_updateInReview)
        self.ui.lineEdit.textChanged.connect(self.ui_wordsNumChanged)
        self.wordsNumChanged = False
        self.ui.lineEdit.returnPressed.connect(self.ui_wordsNumEnterPressed)
        self.ui.pushButton_4.clicked.connect(self.ui_onGoClicked)
        # 听力页面相关
        self.ui.pushButton_5.clicked.connect(self.ui_onSentencePrevClicked)
        self.ui.pushButton_6.clicked.connect(self.ui_onSentenceNextClicked)
        self.ui.lineEdit_2.textChanged.connect(self.fun_initListening)
        self.ui.lineEdit_2.returnPressed.connect(self.ui_sentenceFromEnterPressed)
        self.ui.lineEdit_3.textChanged.connect(self.fun_initListening)
        self.ui.lineEdit_3.returnPressed.connect(self.ui_sentenceToEnterPressed)
        self.ui.pushButton_7.clicked.connect(self.ui_saveClicked)  
        self.ui.pushButton_8.clicked.connect(self.ui_loadConfig)
        self.ui.textEdit_4.textChanged.connect(self.ui_onListeningPageChanged)
        self.ui.progressBar_2.setMinimum(int(self.ui.lineEdit_2.text().strip()))
        self.ui.progressBar_2.setMaximum(int(self.ui.lineEdit_3.text().strip()))
        self.listenPracticeCnt = int(self.ui.lineEdit_3.text().strip()) - int(self.ui.lineEdit_2.text().strip())
        self.fun_initListening()
        # 字体设置
        self.fontSize = 15
        self.ui.fontComboBox.currentFontChanged.connect(self.ui_onFontChanged)
        self.selectFont        = None
        # 单词 textEdit 相关变量
        self.ui.textEdit.textChanged.connect(self.ui_onTextEditChanged)
        self.input_word = None
        self.wordFormat = self.ui.textEdit.currentCharFormat()
        self.wordCursor = self.ui.textEdit.textCursor()
        # 句子 textEdit_2 相关变量
        self.ui.textEdit_2.textChanged.connect(self.ui_onTextEdit_2Changed)
        self.input_sentence  = None
        self.sentenceFormat  = self.ui.textEdit_2.currentCharFormat()
        self.sentenceCursor  = self.ui.textEdit_2.textCursor()
        self.tipListenFormat = self.ui.textEdit_5.currentCharFormat()
        self.tipListenCursor = self.ui.textEdit_5.textCursor()
        # 界面按钮的 signal-slot 连接
        self.ui.pushButton.clicked.connect(self.ui_onPrevClicked)
        self.ui.pushButton_2.clicked.connect(self.ui_onNextClicked)
        self.ui.pushButton_3.clicked.connect(self.ui_getReport)
        # 进度条初始化
        self.ui.progressBar.setMinimum(1)
        self.ui.progressBar.setMaximum(self.wordsNum)
        # 单词错误提示 textEdit 相关变量
        self.tipFormat = self.ui.textEdit_3.currentCharFormat()
        self.tipCursor = self.ui.textEdit_3.textCursor()
        self.fun_getNewWords()
        # 初始化界面上的文字信息
        self.ui_setWordFromIndex(self.wordIndex)
        # 读取配置文件
        self.noConfigFile = True
        import os
        if os.path.exists("config/Settings.json"):
            self.ui_loadConfig()
        else:
            self.ui.tabWidget.setStyleSheet("color:saddlebrown;")

    def ui_loadConfig(self):
        # 读取配置文件
        self.noConfigFile = False
        try:
            with open("config/Settings.json","r",encoding='utf-8') as file:
                self.configDict = json.load(file)
                if len(self.configDict) > 0:
                    self.fun_initWithConfig()
        except (RuntimeError, IOError) as e:
            self.noConfigFile = True
            print(e)
            #out, err = self._proc.communicate()
            #raise IOError('Error saving animation to file (cause: {0}) '
            #          'Stdout: {1} StdError: {2}. It may help to re-run '
            #          'with --verbose-debug.'.format(e, out, err))

    def ui_saveClicked(self):
        self.f_writeConfigFile()

    def fun_initWithConfig(self):
        self.useSentenceScore = self.configDict.get("sentence")
        self.ui.checkBox.setChecked(self.useSentenceScore)
        # 设置模式
        #if self.configDict.get("Ebbinghaus"):
        #    self.wordMode = 2
        #elif self.configDict.get("Review"):
        #    self.wordMode = 1
        #elif self.configDict.get("New"):
        #    self.wordMode = 0
        self.wordMode = 1
        # 设置颜色
        self.updateInReview   = self.configDict.get("UpdateInReview")
        self.ui.checkBox_2.setChecked(self.updateInReview)
        if self.updateInReview:
            self.ui.tabWidget.setStyleSheet("color:purple;")
        elif self.wordMode == 2:
            self.ui.tabWidget.setStyleSheet("color:darkgreen;")
        elif self.wordMode == 1:
            self.ui.tabWidget.setStyleSheet("color:saddlebrown;")
        elif self.wordMode == 0:
            self.ui.tabWidget.setStyleSheet("")
        # 设置复选框，并使模式设置生效
        if self.wordMode == 2:
            self.ui.radioButton.setChecked(True)
            self.ui_selectEbbinghaus()
        elif self.wordMode == 1:
            self.ui.radioButton_2.setChecked(True)
            self.ui_selectReview()
        elif self.wordMode == 0:
            self.ui.radioButton_3.setChecked(True)
            self.ui_selectNew()
        self.practiceMode = EnglishPractice.practiceModeList[self.wordMode]
        self.wordsNum     = self.configDict.get("Count")
        self.ui.lineEdit.setText(str(self.wordsNum))
        self.ui.comboBox.setCurrentIndex(EnglishPractice.vocabulary_list.index(self.configDict.get("Source")))
        # 听力设置恢复
        self.ui.comboBox_2.setCurrentIndex(EnglishPractice.listening_list.index(self.configDict.get("Source2")))
        self.ui.lineEdit_2.setText(str(self.configDict.get("From")))
        self.ui.lineEdit_3.setText(str(self.configDict.get("To")))
        self.ui.progressBar_2.setMinimum(int(self.ui.lineEdit_2.text().strip()))
        self.ui.progressBar_2.setMaximum(int(self.ui.lineEdit_3.text().strip()))
        self.listenPracticeCnt = int(self.ui.lineEdit_3.text().strip()) - int(self.ui.lineEdit_2.text().strip())
    
    def f_writeConfigFile(self):
        with open("config/Settings.json","w",encoding='utf-8') as file:
            self.configDict = {"Source":self.ui.comboBox.currentText(),
                                "Count":int(self.ui.lineEdit.text().strip()) if len(self.ui.lineEdit.text().strip()) > 0 else 1,
                                "Ebbinghaus":self.ui.radioButton.isChecked(),
                                "Review":self.ui.radioButton_2.isChecked(),
                                "New":self.ui.radioButton_3.isChecked(),
                                "sentence":self.ui.checkBox.isChecked(),
                                "UpdateInReview":False,#self.ui.checkBox_2.isChecked(),
                                "Source2":self.ui.comboBox_2.currentText(),
                                "From":int(self.ui.lineEdit_2.text().strip()) if len(self.ui.lineEdit_2.text().strip()) > 0 else 1,
                                "To":int(self.ui.lineEdit_3.text().strip()) if len(self.ui.lineEdit_3.text().strip()) > 0 else 2
                                }
            json.dump(self.configDict,file)

    def ui_renewUI(self,getNewWords = True):
        self.ui.textEdit.clear()
        self.ui.textEdit_2.clear()
        self.ui.textEdit_3.clear()
        self.wordIndex        = 0
        self.words_p_lines    = ''
        self.score            = 0
        if getNewWords:
            self.fun_getNewWords()
        # 初始化界面上的文字信息
        self.ui_setWordFromIndex(self.wordIndex)
        
    def ui_selectEbbinghaus(self):
        self.ui.checkBox.setEnabled(True)
        if self.ui.radioButton.isChecked():
            self.radioButtonChanged = True
        self.wordMode = 2
        self.practiceMode = EnglishPractice.practiceModeList[self.wordMode]
        self.ui.checkBox_2.setChecked(False)
        self.ui.checkBox_2.setVisible(False)
        if self.updateInReview:
            self.ui.tabWidget.setStyleSheet("color:purple;")
        elif self.wordMode == 2:
            self.ui.tabWidget.setStyleSheet("color:darkgreen;")
        elif self.wordMode == 1:
            self.ui.tabWidget.setStyleSheet("color:saddlebrown;")
        elif self.wordMode == 0:
            self.ui.tabWidget.setStyleSheet("")
        self.wordIndex = 0
        self.p_list    = []
        self.ui_renewUI()
        if self.ui.radioButton.isChecked():
            self.f_writeConfigFile()

    def ui_onGoClicked(self):
        import webbrowser
        webbrowser.open(self.db.getListenLink(self.idxListen))
        self.user_inputs = {}
        self.listenIndex = 0
        self.idxListen   = int(self.ui.lineEdit_2.text().strip()) - 1
        self.ui.progressBar_2.setMinimum(int(self.ui.lineEdit_2.text().strip()))
        self.ui.progressBar_2.setMaximum(int(self.ui.lineEdit_3.text().strip()))
        self.listenPracticeCnt = int(self.ui.lineEdit_3.text().strip()) - int(self.ui.lineEdit_2.text().strip())
        self.ui.progressBar_2.setValue(self.idxListen+1)
        self.ui.textBrowser_2.setText(self.db.getListenTranslation(self.idxListen))
        self.ui.textEdit_4.clear()
        self.ui.tabWidget.setCurrentIndex(1)
        self.ui.textEdit_4.setFocus()

    def ui_onSentencePrevClicked(self):
        if self.listenIndex > 0:
            self.listenIndex -= 1
            self.idxListen   -= 1
            self.currentListening = self.db.getListenSentence(self.idxListen)
        self.ui.progressBar_2.setValue(self.idxListen+1)
        self.ui.textBrowser_2.setText(self.db.getListenTranslation(self.idxListen))
        self.ui.textEdit_4.clear()
        if len(self.user_inputs[self.idxListen]) > 0:
            self.ui.textEdit_4.textCursor().insertText(self.user_inputs[self.idxListen])

    def ui_onSentenceNextClicked(self):
        self.user_inputs[self.idxListen] = self.input_listening.strip()
        if self.listenIndex < self.listenPracticeCnt:
            self.listenIndex += 1
            self.idxListen   += 1
            self.currentListening = self.db.getListenSentence(self.idxListen)
            self.ui.textEdit_4.clear()
            if self.user_inputs.get(self.idxListen) is not None:
                if len(self.user_inputs[self.idxListen]) > 0:
                    self.ui.textEdit_4.textCursor().insertText(self.user_inputs[self.idxListen])
        self.ui.progressBar_2.setValue(self.idxListen+1)
        self.ui.textBrowser_2.setText(self.db.getListenTranslation(self.idxListen))

    def fun_initListening(self):
        if len(self.ui.lineEdit_2.text().strip()) > 0:
            self.idxListen = int(self.ui.lineEdit_2.text().strip()) - 1
            self.currentListening = self.db.getListenSentence(self.idxListen)
            self.ui.textBrowser_2.setText(self.db.getListenTranslation(self.idxListen))
            self.user_inputs = {}
            for i in range(self.listenPracticeCnt+1):
                self.user_inputs[i+self.idxListen] = ''

    def ui_onListeningPageChanged(self):
        '''
        输入听到的句子发生变化时的回调函数。
        '''
        self.input_listening = self.ui.textEdit_4.toPlainText()
        replace_pos, delete_pos, insert_pos = self.fun_diffWord(self.input_listening, self.currentListening)

        # 修改窗口的提示
        self.ui.textEdit_5.clear()
        if not replace_pos and not delete_pos and not insert_pos:
            self.tipListenFormat.setForeground(QColor("green"))
            self.tipListenCursor.insertText("Excellent!")
            self.tipListenCursor.setPosition(0,QTextCursor.MoveAnchor)
            self.tipListenCursor.setPosition(10,QTextCursor.KeepAnchor)
            self.tipListenCursor.mergeCharFormat(self.tipListenFormat)
        else:
            tipString = self.input_listening
            # 需插入的地方用 _ 代替
            insert_pos.reverse()
            #print(insert_pos,tipString)
            for i in range(len(insert_pos)):
                index = insert_pos[i][2]
                times = insert_pos[i][1]-insert_pos[i][0]
                tipString = list(tipString)
                tipString.insert(index, '_'*times)
                tipString = ''.join(tipString)
            # 修改 tipString 后重新对比
            self.ui.textEdit_5.clear()
            self.tipListenCursor.insertText(tipString)
            replace_pos, delete_pos, insert_pos = self.fun_diffWord(tipString, self.currentListening)
            # 删除多余字母
            delete_pos.reverse()
            #print(delete_pos,tipString)
            for i in range(len(delete_pos)):
                index = delete_pos[i][0]
                times = delete_pos[i][1]-delete_pos[i][0]
                tipString = tipString[:index] + tipString[index+times:]
            # 修改 tipString 后重新对比
            self.ui.textEdit_5.clear()
            self.tipListenCursor.insertText(tipString)
            replace_pos, delete_pos, insert_pos = self.fun_diffWord(tipString, self.currentListening)
            # 处理需替换的内容
            replace_pos.reverse()
            #print(replace_pos,tipString)
            self.tipListenFormat.setForeground(QColor("red"))
            for i in range(len(replace_pos)):
                # 若替换内容与被替换内容个数相同，则用红字标示。
                if replace_pos[i][3] - replace_pos[i][2] == replace_pos[i][1] - replace_pos[i][0]:
                    self.tipListenCursor.setPosition(replace_pos[i][0],QTextCursor.MoveAnchor)
                    self.tipListenCursor.setPosition(replace_pos[i][1],QTextCursor.KeepAnchor)
                    self.tipListenCursor.mergeCharFormat(self.tipListenFormat)
                else: # 若替换内容与被替换内容个数不同，则先从目标删除
                    index = replace_pos[i][0]
                    times1 = replace_pos[i][1]-replace_pos[i][0]
                    tipString = tipString[:index] + tipString[index+times1:]
                    # 再把需要替换的位置填上 _
                    times2 = replace_pos[i][3]-replace_pos[i][2]
                    tipString = list(tipString)
                    tipString.insert(index, '_'*times2)
                    tipString = ''.join(tipString)
                    # 如果填的 _ 个数多于删除的个数，则多出几个就在末尾截出几个(用 _ 代替)
                    if times2 > times1:
                        times_error = times2 - times1
                        tipString = tipString[:-1]+'_'*times_error
                    self.ui.textEdit_5.clear()
                    self.tipListenCursor.insertText(tipString)
        if len(self.input_listening) > 0:
            if '\t' == self.input_listening[-1]:
                self.ui_onSentenceNextClicked()

    def ui_selectReview(self):
        self.ui.checkBox_2.setVisible(True)
        if self.ui.checkBox_2.isChecked():
            if self.ui.checkBox.isChecked() == False:
                self.ui.checkBox.setChecked(False)
            else:
                self.ui.checkBox.setEnabled(True)
        else:
            self.ui.checkBox.setChecked(False)
            self.ui.checkBox.setEnabled(False)
        self.wordMode = 1
        self.practiceMode = EnglishPractice.practiceModeList[self.wordMode]
        if self.updateInReview:
            self.ui.tabWidget.setStyleSheet("color:purple;")
        elif self.wordMode == 2:
            self.ui.tabWidget.setStyleSheet("color:darkgreen;")
        elif self.wordMode == 1:
            self.ui.tabWidget.setStyleSheet("color:saddlebrown;")
        elif self.wordMode == 0:
            self.ui.tabWidget.setStyleSheet("")
        self.wordIndex = 0
        self.p_list    = []
        self.ui_renewUI()
        if self.radioButtonChanged and self.ui.radioButton_2.isChecked():
            self.f_writeConfigFile()

    def ui_selectNew(self):
        self.ui.checkBox_2.setVisible(True)
        if self.ui.checkBox_2.isChecked():
            if self.ui.checkBox.isChecked() == False:
                self.ui.checkBox.setChecked(False)
            else:
                self.ui.checkBox.setEnabled(True)
        else:
            self.ui.checkBox.setChecked(False)
            self.ui.checkBox.setEnabled(False)
        if self.ui.radioButton_3.isChecked():
            self.radioButtonChanged = True
        self.wordMode = 0
        self.practiceMode = EnglishPractice.practiceModeList[self.wordMode]
        if self.updateInReview:
            self.ui.tabWidget.setStyleSheet("color:purple;")
        elif self.wordMode == 2:
            self.ui.tabWidget.setStyleSheet("color:darkgreen;")
        elif self.wordMode == 1:
            self.ui.tabWidget.setStyleSheet("color:saddlebrown;")
        elif self.wordMode == 0:
            self.ui.tabWidget.setStyleSheet("")
        self.wordIndex = 0
        self.p_list    = []
        self.ui_renewUI()
        if self.ui.radioButton_3.isChecked():
            self.f_writeConfigFile()

    def ui_sentenceMode(self):
        if self.ui.checkBox.isChecked():
            self.checkBoxInitiated = True
        self.useSentenceScore = self.ui.checkBox.isChecked()
        if self.useSentenceScore:
            self.ui.label_3.setStyleSheet("color:red;")
            font = self.ui.label_3.font()
            font.setPointSize(15)
            self.ui.label_3.setFont(font)
        else:
            self.ui.label_3.setStyleSheet("color:black;")
            font = self.ui.label_3.font()
            font.setPointSize(9)
            self.ui.label_3.setFont(font)
        if self.wordMode == 2:
            self.ui_renewUI()
        if self.checkBoxInitiated:
            self.f_writeConfigFile()

    def ui_updateInReview(self):
        if self.ui.checkBox_2.isChecked():
            self.checkBox_2Initiated = True
        if self.wordMode != 2:
            if self.ui.checkBox_2.isChecked() == False:
                self.ui.checkBox.setChecked(False)
                self.ui.checkBox.setEnabled(False)
            else:
                self.ui.checkBox.setEnabled(True)
        self.updateInReview = self.ui.checkBox_2.isChecked()
        if self.updateInReview:
            self.ui.tabWidget.setStyleSheet("color:purple;")
        elif self.wordMode == 2:
            self.ui.tabWidget.setStyleSheet("color:darkgreen;")
        elif self.wordMode == 1:
            self.ui.tabWidget.setStyleSheet("color:saddlebrown;")
        elif self.wordMode == 0:
            self.ui.tabWidget.setStyleSheet("")
        self.ui_renewUI(False)
        if self.checkBox_2Initiated:
            self.f_writeConfigFile()

    def ui_wordsNumChanged(self):
        if len(self.ui.lineEdit.text().strip()) > 0:
            self.wordsNum  = int(self.ui.lineEdit.text())
            self.wordIndex = 0
            self.p_list    = []
            self.ui_renewUI()

    def ui_wordsNumEnterPressed(self):
        if len(self.ui.lineEdit.text().strip()) > 0:
            self.wordsNumChanged = True
            self.f_writeConfigFile()
            self.ui_loadConfig()
            self.ui.tabWidget.setCurrentIndex(0)
            self.ui.textEdit.setFocus()

    def ui_sentenceFromEnterPressed(self):
        self.f_writeConfigFile()

    def ui_sentenceToEnterPressed(self):
        self.f_writeConfigFile()

    def fun_getNewWords(self):
        # 获取新词汇
        res = self.fun_initWords()
        if res == False:
            self.fun_initWords(True)

    def fun_initWords(self, force_from_db = False):
        res = False
        self.ebdb.open()
        self.ebWords   = self.ebdb.getWords(self.useSentenceScore)
        self.ebdb.close()
        if self.practiceMode == EnglishPractice.practiceModeList[0] or force_from_db:
            res = True
            # 从数据库中取数据
            self.words       = self.db.get_randomly(self.wordsNum,self.ebWords)
            if self.generateAllWords:
                self.words   = self.db.getAllWords()
            # 生成单词文件
            self.db_getWords()
            self.f_generateWords()
        elif self.practiceMode == EnglishPractice.practiceModeList[1]:
            res = self.f_getWords()
        elif self.practiceMode == EnglishPractice.practiceModeList[2]:
            res = self.eb_getEbbinghausWords()
        if len(self.words) > 0:
            self.currentWord = self.words[self.wordIndex]
        return res

    def eb_getEbbinghausWords(self):
        result = False
        selectedWords = []
        # 逐一检查是否满足 Ebbinghaus 标准
        cnt = 0
        if self.noConfigFile == False:
            if self.wordsNumChanged or self.radioButtonChanged:
                self.wordsNum     = int(self.ui.lineEdit.text())
            else:
                self.wordsNum     = self.configDict.get("Count")
            # 进度条初始化
            self.ui.progressBar.setMinimum(1)
            self.ui.progressBar.setMaximum(self.wordsNum)
        for word in self.ebWords:
            if self.useSentenceScore == False:
                res = self.ebbinghaus.check(self.ebdb.wordCount(word), self.ebdb.wordTimestamp(word))
            else:
                sentenceTimestamp = self.ebdb.sentenceTimestamp(word)
                if sentenceTimestamp is None:
                    res = True
                else:
                    res = self.ebbinghaus.check(self.ebdb.sentenceCount(word), sentenceTimestamp, self.ebdb.score(word))
            if res == True:
                selectedWords.append(word)
                cnt += 1
                if cnt >= self.wordsNum:
                    break
        self.words = selectedWords[:self.wordsNum]
        if len(self.words) > 0:
            result = True
            self.db_getWords()
            self.f_generateWords()
            if len(self.words) < self.wordsNum:
                self.wordsNum = len(self.words)
                # 进度条初始化
                self.ui.progressBar.setMinimum(1)
                self.ui.progressBar.setMaximum(self.wordsNum)
        return result

    def ui_wordSourceChanged(self):
        self.db.getWords(self.ui.comboBox.currentText())

    def ui_setWordFont(self):
        '''
        设置单词输入框和提示框的字体
        被 ui_onFontChanged() 和 ui_onTextEditChanged() 调用
        '''
        if self.selectFont is not None:
            # 设置单词输入框字体
            self.wordFormat.setFontFamily(self.selectFont)
            self.wordFormat.setFontFamilies(list(self.selectFont))
            self.ui.textEdit.setCurrentCharFormat(self.wordFormat)
            # 设置句子输入框字体
            self.sentenceFormat.setFontFamily(self.selectFont)
            self.sentenceFormat.setFontFamilies(list(self.selectFont))
            self.ui.textEdit_2.setCurrentCharFormat(self.sentenceFormat)
            # 设置提示框字体
            self.tipFormat.setFontFamily(self.selectFont)
            self.tipFormat.setFontFamilies(list(self.selectFont))
            self.ui.textEdit_3.setCurrentCharFormat(self.tipFormat)
        
    def ui_onFontChanged(self, font):
        '''
        响应字体改变的 slot 函数
        '''
        # 设置汉语意思标签字体
        #self.ui.label.setFont(QFont(font.family(), self.fontSize))
        
        self.selectFont = font.family()
        # 对单词框获取已有的输入内容存入 lineContent 变量
        self.wordCursor.select(QTextCursor.LineUnderCursor)
        lineContent = self.wordCursor.selectedText()
        # 删除输入内容
        self.ui.textEdit.clear()
        self.ui_setWordFont()
        # 还原输入内容
        self.wordCursor.insertText(lineContent, self.wordFormat)

        # 对句子框获取已有的输入内容存入 lineContent 变量
        self.sentenceCursor.select(QTextCursor.Document)
        lineContent = self.sentenceCursor.selectedText()
        # 删除输入内容
        self.ui.textEdit_2.clear()
        self.ui_setWordFont()
        # 还原输入内容
        self.sentenceCursor.insertText(lineContent, self.sentenceFormat)
        
    def ui_onTextEditChanged(self):
        '''
        输入单词发生变化时的回调函数。
        '''
        self.ui_setWordFont() 
        self.input_word = self.ui.textEdit.toPlainText()
        replace_pos, delete_pos, insert_pos = self.fun_diffWord(self.input_word, self.currentWord)

        # 修改窗口的提示
        self.tipFormat.setFontStrikeOut(False) # 删除线
        self.ui.textEdit_3.clear()
        if not replace_pos and not delete_pos and not insert_pos:
            self.tipFormat.setForeground(QColor("green"))
            self.tipCursor.insertText("Excellent!")
            self.tipCursor.setPosition(0,QTextCursor.MoveAnchor)
            self.tipCursor.setPosition(10,QTextCursor.KeepAnchor)
            self.tipCursor.mergeCharFormat(self.tipFormat)
        else:
            tipString = self.input_word
            # 需插入的地方用 _ 代替
            insert_pos.reverse()
            #print(insert_pos,tipString)
            for i in range(len(insert_pos)):
                index = insert_pos[i][2]
                times = insert_pos[i][1]-insert_pos[i][0]
                tipString = list(tipString)
                tipString.insert(index, '_'*times)
                tipString = ''.join(tipString)
            # 修改 tipString 后重新对比
            self.ui.textEdit_3.clear()
            self.tipCursor.insertText(tipString)
            replace_pos, delete_pos, insert_pos = self.fun_diffWord(tipString, self.currentWord)
            # 删除多余字母
            delete_pos.reverse()
            #print(delete_pos,tipString)
            for i in range(len(delete_pos)):
                index = delete_pos[i][0]
                times = delete_pos[i][1]-delete_pos[i][0]
                tipString = tipString[:index] + tipString[index+times:]
            # 修改 tipString 后重新对比
            self.ui.textEdit_3.clear()
            self.tipCursor.insertText(tipString)
            replace_pos, delete_pos, insert_pos = self.fun_diffWord(tipString, self.currentWord)
            # 处理需替换的内容
            replace_pos.reverse()
            #print(replace_pos,tipString)
            self.tipFormat.setForeground(QColor("red"))
            #self.tipFormat.setFontStrikeOut(True) # 删除线
            for i in range(len(replace_pos)):
                # 若替换内容与被替换内容个数相同，则用红字标示。
                if replace_pos[i][3] - replace_pos[i][2] == replace_pos[i][1] - replace_pos[i][0]:
                    self.tipCursor.setPosition(replace_pos[i][0],QTextCursor.MoveAnchor)
                    self.tipCursor.setPosition(replace_pos[i][1],QTextCursor.KeepAnchor)
                    self.tipCursor.mergeCharFormat(self.tipFormat)
                else: # 若替换内容与被替换内容个数不同，则先从目标删除
                    index = replace_pos[i][0]
                    times1 = replace_pos[i][1]-replace_pos[i][0]
                    tipString = tipString[:index] + tipString[index+times1:]
                    # 再把需要替换的位置填上 _
                    times2 = replace_pos[i][3]-replace_pos[i][2]
                    tipString = list(tipString)
                    tipString.insert(index, '_'*times2)
                    tipString = ''.join(tipString)
                    # 如果填的 _ 个数多于删除的个数，则多出几个就在末尾截出几个(用 _ 代替)
                    if times2 > times1:
                        times_error = times2 - times1
                        tipString = tipString[:-1]+'_'*times_error
                    self.ui.textEdit_3.clear()
                    self.tipCursor.insertText(tipString)
        if '\n' in self.input_word:
            tempWord = self.input_word
            self.ui.textEdit.clear()
            self.wordCursor.insertText(tempWord.strip())
            self.ui.textEdit_2.setFocus()
        if '\t' in self.input_word:
            self.ui_onNextClicked()

    def ui_onTextEdit_2Changed(self):
        '''
        输入句子发生变化时的回调函数。
        '''
        self.input_sentence = self.ui.textEdit_2.toPlainText()
        self.fun_diffSentence(self.input_sentence,self.sentences.get(self.currentWord))
        if '\t' in self.input_sentence:
            self.ui_onNextClicked()

    def fun_diffWord(self, input_word, word):
        '''
        https://learnku.com/docs/pymotw/difflib-character-comparison/3363
        '''
        import difflib
        matcher = difflib.SequenceMatcher(None, input_word.strip(), word.strip())
        replace_positions = []
        delete_positions  = []
        insert_positions  = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                replace_positions.append([i1, i2, j1, j2])
            if tag == 'delete':
                delete_positions.append([i1, i2])
            if tag == 'insert':
                insert_positions.append([j1, j2, i1])

        return replace_positions, delete_positions, insert_positions

    def fun_diffSentence(self, input_sentence, sentence):
        import difflib
        self.score = difflib.SequenceMatcher(None, input_sentence.strip(), sentence.strip()).quick_ratio()
        self.ui_setScore('%.2f'%(self.score))

    def ui_setScore(self,score):
        self.ui.label_3.setText(score)

    def ui_onPrevClicked(self):
        if self.wordIndex > 0:
            self.wordIndex -= 1
            self.ui_setWordFromIndex(self.wordIndex)

            # 恢复输入内容
            self.ui.textEdit.clear()
            self.wordCursor.insertText(self.p_list[8*self.wordIndex].strip())
            self.ui.textEdit_2.clear()
            self.sentenceCursor.insertText(self.p_list[8*self.wordIndex+5].strip())

    def ui_onNextClicked(self):
        # 在 p_list 中保存输入内容
        if self.input_word is not None:
            self.p_list[self.wordIndex*8] = self.input_word.rstrip()+'\n'
        if self.input_sentence is not None:
            self.p_list[self.wordIndex*8+5] = self.input_sentence.rstrip()+'\n'
        # 写练习文件
        self.f_wordsToFile()
        if self.wordMode == 2 or self.updateInReview:
            # 写 Ebbinghaus 数据库
            self.db_writeEbbinghausDB()
        if self.wordIndex < self.wordsNum - 1:
            self.wordIndex += 1
            self.ui_setWordFromIndex(self.wordIndex)

            # 恢复输入内容
            self.ui.textEdit.clear()
            self.wordCursor.insertText(self.p_list[8*self.wordIndex].strip())
            self.ui.textEdit_2.clear()
            self.sentenceCursor.insertText(self.p_list[8*self.wordIndex+5].strip())

            self.ui.textEdit.setFocus()

    def ui_getReport(self):
        self.ebdb.open()
        words_report = self.ebdb.getWords(self.useSentenceScore)
        from datetime import datetime
        with open("reports/"+str(datetime.now()).replace(':','-')+".html","w",encoding='utf-8') as file:
            file.write('<table>\n')
            file.write('''    <tr align="left">
        <th bgcolor="#F6F6F6"> Word</th>
        <th bgcolor="#F6F6F6"> <font color="#FE642E"> Score</th>
        <th bgcolor="#F6F6F6"> <font color="#04B431"> Word Count</th>
        <th bgcolor="#F6F6F6"> <font color="#045FB4"> Sentence Count</th>
    </tr>''')
            index = 0
            for word in words_report:
                if index % 2 == 0:
                    file.write('''
    <tr >
        <td bgcolor="#FDFDFD"> %s</td>
        <td bgcolor="#FDFDFD"> <font color="#FE642E">%s</td>
        <td bgcolor="#FDFDFD"> <font color="#04B431">%s</td>
        <td bgcolor="#FDFDFD"> <font color="#045FB4">%s</td>
    </tr>'''%(word,str(self.ebdb.score(word)),str(self.ebdb.wordCount(word)), str(self.ebdb.sentenceCount(word))))
                else:
                    file.write('''
    <tr >
        <td bgcolor="#F6F6F6"> %s</td>
        <td bgcolor="#F6F6F6"> <font color="#FE642E">%s</td>
        <td bgcolor="#F6F6F6"> <font color="#04B431">%s</td>
        <td bgcolor="#F6F6F6"> <font color="#045FB4">%s</td>
    </tr>'''%(word,str(self.ebdb.score(word)),str(self.ebdb.wordCount(word)), str(self.ebdb.sentenceCount(word))))
                index += 1
            file.write('\n</table>\n')
        self.ebdb.close()

    def ui_setWordFromIndex(self, index):
        self.currentWord = self.words[index]
        self.ui_setMeaning()
        self.ui_setPronun()
        self.ui_setTrans()
        self.ui.progressBar.setValue(index+1)
    def ui_setMeaning(self):
        self.ui.label.setText(self.meanings.get(self.currentWord))
    def ui_setPronun(self):
        self.ui.label_2.setText(self.pronunciations.get(self.currentWord))
    def ui_setSentence(self):
        self.ui.textEdit_2.clear()
        self.ui.textEdit_2.textCursor().insertText(self.sentences.get(self.currentWord))
    def ui_setTrans(self):
        self.ui.textBrowser.setText(self.translations.get(self.currentWord))

    def db_getWords(self):
        for word in self.words:
            self.pronunciations[word] = self.db.pronun(word)
            self.meanings      [word] = self.db.mean(word)
            self.sentences     [word] = self.db.sentence(word)
            self.translations  [word] = self.db.trans(word)

    def f_getWords(self):
        self.p_list = []
        res = True
        try:
            with open("EnglishFiles/words.txt","r",encoding='utf-8') as file:
                word = None
                for i, line in enumerate(file):
                    content = line.strip()
                    if i % 5 == 0:
                        word = content
                        self.words.append(content)
                        self.p_list.append('\n')
                    if i % 5 == 1:
                        self.pronunciations[word] = content
                        self.p_list.append(content)
                        self.p_list.append('\n')
                    if i % 5 == 2:
                        self.meanings[word] = content
                        self.p_list.append(content)
                        self.p_list.append('\n')
                    if i % 5 == 3:
                        self.sentences[word] = content
                        self.p_list.append('\n')
                    if i % 5 == 4:
                        self.translations[word] = content
                        self.p_list.append(content)
                        self.p_list.append('\n')

            self.wordsNum = int((i+1)/5)
            # 进度条初始化
            self.ui.progressBar.setMinimum(1)
            self.ui.progressBar.setMaximum(self.wordsNum)
        except:
            res = False
        return res

    def db_writeEbbinghausDB(self):
        input_word = self.input_word.strip()
        word_cnt = self.ebdb.wordCount(input_word)
        if word_cnt is None:
            word_cnt = 1
        else:
            word_cnt += 1
        sentence_cnt = self.ebdb.sentenceCount(input_word)
        if sentence_cnt is None:
            sentence_cnt = 1
        elif self.score > self.sentenceCriteria:
            sentence_cnt += 1
        from datetime import datetime
        if len(input_word) > 0 and self.pronunciations.get(input_word) is not None:
            if self.useSentenceScore == False:
                sentenceTimestamp = self.ebdb.sentenceTimestamp(input_word)
                sentence_cnt = self.ebdb.sentenceCount(input_word)
                self.writeEbbinghaus.openAndInsert(input_word,
                                                   self.score,
                                                   word_cnt,
                                                   sentence_cnt,
                                                   datetime.now(),
                                                   sentenceTimestamp)
            elif self.score > self.sentenceCriteria:
                self.writeEbbinghaus.openAndInsert(input_word,
                                                   self.score,
                                                   word_cnt,
                                                   sentence_cnt,
                                                   datetime.now(),
                                                   datetime.now())
    def f_wordsToFile(self):
        self.words_p_lines = ''
        with open("EnglishFiles/words_p.txt","w",encoding='utf-8') as file:
            for i in self.p_list:
                self.words_p_lines += i
            file.write(self.words_p_lines.rstrip())
    def f_generateWords(self):
        self.words_p_lines = ''
        with open("EnglishFiles/words.txt","w",encoding='utf-8') as file:
            for word in self.words:
                self.words_p_lines += word
                self.words_p_lines += '\n'
                self.words_p_lines += self.pronunciations.get(word)
                self.words_p_lines += '\n'
                self.words_p_lines += self.meanings.get(word)
                self.words_p_lines += '\n'
                self.words_p_lines += self.sentences.get(word)
                self.words_p_lines += '\n'
                self.words_p_lines += self.translations.get(word)
                self.words_p_lines += '\n'
            file.write(self.words_p_lines.rstrip())
        self.words_p_lines = ''
        with open("EnglishFiles/words_p.txt","w",encoding='utf-8') as file:
            for word in self.words:
                self.p_list.append('\n')
                self.p_list.append(self.pronunciations.get(word))
                self.p_list.append('\n')
                self.p_list.append(self.meanings.get(word))
                self.p_list.append('\n')
                self.p_list.append('\n')
                self.p_list.append(self.translations.get(word))
                self.p_list.append('\n')
            for i in self.p_list:
                self.words_p_lines += i
            file.write(self.words_p_lines.rstrip())

app = QApplication([])
app.setWindowIcon(QIcon('config/icon.ico'))
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("starter")
ep = EnglishPractice()
ep.ui.show()
app.exec_()