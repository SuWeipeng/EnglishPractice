from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QTextCursor, QColor
from PyQt5 import uic
from modules.ReadWordFromDB import ReadWordFromDB

class EnglishPractice:
    practiceModeList = ['new','review']
    def __init__(self):
        self.words            = []
        self.pronunciations   = {}
        self.meanings         = {}
        self.sentences        = {}
        self.translations     = {}
        self.practiceMode     = EnglishPractice.practiceModeList[0] 
        self.wordsNum         = 10
        self.wordIndex        = 0
        self.words_p_lines    = ''
        self.p_list           = []
        # 从 UI 定义中动态 创建一个相应的窗口对象
        self.ui = uic.loadUi("ui/EnglishPractice.ui")
        # 字体设置
        self.fontSize = 15
        self.ui.fontComboBox.currentFontChanged.connect(self.onFontChanged)
        self.selectFont        = None
        # 单词 textEdit 相关变量
        self.ui.textEdit.textChanged.connect(self.onTextEditChanged)
        self.input_word = None
        self.wordFormat = self.ui.textEdit.currentCharFormat()
        self.wordCursor = self.ui.textEdit.textCursor()
        # 界面按钮的 signal-slot 连接
        self.ui.pushButton.clicked.connect(self.onPrevClicked)
        self.ui.pushButton_2.clicked.connect(self.onNextClicked)
        # 进度条初始化
        self.ui.progressBar.setMinimum(1)
        self.ui.progressBar.setMaximum(self.wordsNum)
        # 单词错误提示 textEdit 相关变量
        self.tipFormat = self.ui.textEdit_3.currentCharFormat()
        self.tipCursor = self.ui.textEdit_3.textCursor()
        if self.practiceMode == EnglishPractice.practiceModeList[0]:
            # 从数据库中取数据
            self.db          = ReadWordFromDB("English.db")
            self.words       = self.db.get_randomly(self.wordsNum)            
            # 生成单词文件
            self.getWordsFromDB()
            self.generateWordFile()
        elif self.practiceMode == EnglishPractice.practiceModeList[1]:
            self.getWordsFromFile()
        # 初始化界面上的文字信息
        self.setWordFromIndex(self.wordIndex)

    def setWordFont(self):
        '''
        设置单词输入框和提示框的字体
        被 onFontChanged() 和 onTextEditChanged() 调用
        '''
        if self.selectFont is not None:
            # 设置单词输入框字体
            self.wordFormat.setFontFamily(self.selectFont)
            self.wordFormat.setFontFamilies(list(self.selectFont))
            self.ui.textEdit.setCurrentCharFormat(self.wordFormat)
            # 设置提示框字体
            self.tipFormat.setFontFamily(self.selectFont)
            self.tipFormat.setFontFamilies(list(self.selectFont))
            self.ui.textEdit_3.setCurrentCharFormat(self.tipFormat)
        
    def onFontChanged(self, font):
        '''
        响应字体改变的 slot 函数
        '''
        # 设置汉语意思标签字体
        #self.ui.label.setFont(QFont(font.family(), self.fontSize))
        
        self.selectFont = font.family()
        # 获取已有的输入内容存入 lineContent 变量
        self.wordCursor.select(QTextCursor.LineUnderCursor)
        lineContent = self.wordCursor.selectedText()
        # 删除输入内容
        self.ui.textEdit.clear()
        self.setWordFont()
        # 还原输入内容
        self.wordCursor.insertText(lineContent, self.wordFormat)
        
    def onTextEditChanged(self):
        '''
        输入单词发生变化时的回调函数。
        '''
        self.setWordFont() 
        self.input_word = self.ui.textEdit.toPlainText()
        replace_pos, delete_pos, insert_pos = self.diffWord(self.input_word, self.currentWord)

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
            replace_pos, delete_pos, insert_pos = self.diffWord(tipString, self.currentWord)
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
            replace_pos, delete_pos, insert_pos = self.diffWord(tipString, self.currentWord)
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

    def diffWord(self, input_word, word):
        '''
        https://learnku.com/docs/pymotw/difflib-character-comparison/3363
        '''
        import difflib
        matcher = difflib.SequenceMatcher(None, input_word, word)
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

    def onPrevClicked(self):
        if self.wordIndex > 0:
            self.wordIndex -= 1
            self.setWordFromIndex(self.wordIndex)
    def onNextClicked(self):
        if self.wordIndex < self.wordsNum - 1:
            self.wordIndex += 1
            self.setWordFromIndex(self.wordIndex)
    def setWordFromIndex(self, index):
        self.currentWord = self.words[index]
        self.setMeaning()
        self.setPronun()
        self.setTrans()
        self.ui.progressBar.setValue(index+1)
    def setMeaning(self):
        self.ui.label.setText(self.meanings.get(self.currentWord))
    def setPronun(self):
        self.ui.label_2.setText(self.pronunciations.get(self.currentWord))
    def setSentence(self):
        self.ui.textEdit_2.clear()
        self.ui.textEdit_2.textCursor().insertText(self.sentences.get(self.currentWord))
    def setTrans(self):
        self.ui.textBrowser.setText(self.translations.get(self.currentWord))
    def getWordsFromDB(self):
        for word in self.words:
            self.pronunciations[word] = self.db.pronun(word)
            self.meanings      [word] = self.db.mean(word)
            self.sentences     [word] = self.db.sentence(word)
            self.translations  [word] = self.db.trans(word)
    def getWordsFromFile(self):
        with open("EnglishFiles/words.txt","r",encoding='utf-8') as file:
            word = None
            for i, line in enumerate(file):
                content = line.strip()
                if i % 5 == 0:
                    word = content
                    self.words.append(content)
                if i % 5 == 1:
                    self.pronunciations[word] = content
                if i % 5 == 2:
                    self.meanings[word] = content
                if i % 5 == 3:
                    self.sentences[word] = content
                if i % 5 == 4:
                    self.translations[word] = content
    def generateWordFile(self):
        with open("EnglishFiles/words.txt","w",encoding='utf-8') as file:
            for word in self.words:
                file.write(word)
                file.write('\n')
                file.write(self.pronunciations.get(word))
                file.write('\n')
                file.write(self.meanings.get(word))
                file.write('\n')
                file.write(self.sentences.get(word))
                file.write('\n')
                file.write(self.translations.get(word))
                file.write('\n')
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
            print(self.words_p_lines)

app = QApplication([])
ep = EnglishPractice()
ep.ui.show()
app.exec_()