from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QTextCursor, QColor
from PyQt5 import uic
from modules.ReadWordFromDB import ReadWordFromDB
from modules.WriteEbbinghausDB import WriteEbbinghausDB
from modules.ReadEbbinghausDB import ReadEbbinghausDB
from modules.Ebbinghaus import Ebbinghaus

class EnglishPractice:
    '''
    01. 与 ui 相关的函数名以         ui_ 开头
    02. 与数据库相关的函数名以       db_  开头
    03. 与文件相关的函数名以         f_   开头
    04. 功能相关的函数名以           fun_ 开头
    05. 与 Ebbinghous 相关的函数名以 eb_  开头
    '''
    practiceModeList = ['new','review','ebbinghaus']
    def __init__(self):
        self.words            = []
        self.pronunciations   = {}
        self.meanings         = {}
        self.sentences        = {}
        self.translations     = {}
        self.practiceMode     = EnglishPractice.practiceModeList[2] 
        self.useSentenceScore = True
        self.wordsNum         = 10
        self.wordIndex        = 0
        self.words_p_lines    = ''
        self.p_list           = []
        self.writeEbbinghaus  = WriteEbbinghausDB("Ebbinghaus.db")
        self.ebdb             = ReadEbbinghausDB("Ebbinghaus.db")
        self.score            = 0
        self.ebbinghaus       = Ebbinghaus()
        self.sentenceCriteria = 0.9
        # 从 UI 定义中动态 创建一个相应的窗口对象
        self.ui = uic.loadUi("ui/EnglishPractice.ui")
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
        self.input_sentence = None
        self.sentenceFormat = self.ui.textEdit_2.currentCharFormat()
        self.sentenceCursor = self.ui.textEdit_2.textCursor()
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
        # 初始化词汇
        res = self.fun_initWords()
        if res == False:
            self.fun_initWords(True)
        # 初始化界面上的文字信息
        self.ui_setWordFromIndex(self.wordIndex)

    def fun_initWords(self, force_from_db = False):
        res = False
        # 打开单词数据库
        self.db        = ReadWordFromDB("English.db")
        if self.practiceMode == EnglishPractice.practiceModeList[0] or force_from_db:
            res = True
            # 从数据库中取数据
            self.words       = self.db.get_randomly(self.wordsNum)            
            # 生成单词文件
            self.db_getWords()
            self.f_generateWords()
        elif self.practiceMode == EnglishPractice.practiceModeList[1]:
            res = True
            self.f_getWords()
        elif self.practiceMode == EnglishPractice.practiceModeList[2]:
            res = self.eb_getEbbinghausWords()
        return res

    def eb_getEbbinghausWords(self):
        result = False
        selectedWords = []
        all = self.ebdb.getWords(self.useSentenceScore)
        # 逐一检查是否满足 Ebbinghaus 标准
        cnt = 0
        for word in all:
            if self.useSentenceScore == False:
                res = self.ebbinghaus.check(self.ebdb.wordCount(word), self.ebdb.wordTimestamp(word))
            else:
                res = self.ebbinghaus.check(self.ebdb.sentenceCount(word), self.ebdb.sentenceTimestamp(word), self.ebdb.score(word))
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
        with open("reports/"+str(datetime.now()).replace(':','-')+".txt","w",encoding='utf-8') as file:
            for word in words_report:
                file.write(word+'\t'+str(self.ebdb.score(word))+'\t'+str(self.ebdb.wordCount(word))+'\t'+str(self.ebdb.sentenceCount(word))+'\n')
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
ep = EnglishPractice()
ep.ui.show()
app.exec_()