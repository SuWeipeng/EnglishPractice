from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QFont, QTextCursor, QColor, QIcon
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from modules.ReadWordFromDB import ReadWordFromDB
from modules.WriteEbbinghausDB import WriteEbbinghausDB
from modules.ReadEbbinghausDB import ReadEbbinghausDB
from modules.Ebbinghaus import Ebbinghaus
from modules.AutoTranslator import AutoTranslator
from modules.Youtube import Youtube
import modules.MoodText as MoodText
import json
import pyttsx3
import threading
import os, glob, contextlib
import pyaudio
import wave
import requests
from PyDictionary import PyDictionary

class WAV:
    VALID = False
    def __init__(self,wav_folder):
        if self.f_check_file(wav_folder):
            WAV.VALID = True
        else:
            WAV.VALID = False
    def f_check_file(self,file_path):
        if os.path.exists(file_path):
            return True
        else:
            return False
    def count_wav_files(self, directory):
        # 构建搜索模式来匹配目录中的所有 .wav 文件
        pattern = os.path.join(directory, '*.wav')
        # 使用 glob.glob() 查找所有匹配的文件
        wav_files = glob.glob(pattern)
        # 返回找到的 .wav 文件数量
        return len(wav_files)
    def get_wav_filenames(self, directory):
        # 构建搜索模式以匹配目录中的所有 .wav 文件
        pattern = os.path.join(directory, '*.wav')
        # 使用 glob.glob() 查找所有匹配的文件
        wav_files = glob.glob(pattern)
        # 从完整路径中提取文件名
        wav_filenames = [os.path.basename(wav_file) for wav_file in wav_files]
        # 返回所有找到的 .wav 文件名
        return wav_filenames
    def duration(self, wav_file):
        with contextlib.closing(wave.open(wav_file, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration_s = frames / float(rate)
            return duration_s
    def seconds_to_hms(self,seconds):
        from datetime import timedelta
        res = ""
        # 使用 timedelta 创建一个表示指定秒数的时间差
        td = timedelta(seconds=seconds)
        # 将 timedelta 格式化为小时:分钟:秒
        # 注意：这里使用了 divmod 来分别获取小时和剩余的分钟秒数
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        # 返回格式化的字符串
        if hours > 0:
            res = '{:02}h {:02}min {:02}sec'.format(hours, minutes, seconds)
        elif minutes > 0:
            res = '{:02}min {:02}sec'.format(minutes, seconds)
        else:
            res = '{:02}sec'.format(seconds)
        return res

class EnglishPractice(QWidget):
    '''
    01. 与 ui 相关的函数名以         ui_ 开头
    02. 与数据库相关的函数名以       db_  开头
    03. 与文件相关的函数名以         f_   开头
    04. 功能相关的函数名以           fun_ 开头
    05. 与 Ebbinghous 相关的函数名以 eb_  开头
    06. 与 TTS 相关以               tts_ 开头
    '''
    practiceModeList = ['new','review','ebbinghaus']
    vocabulary_list  = ['IELTS1000','ORCHARD7','ORCHARD6','ORCHARD5','ORCHARD4','ORCHARD3','PHRASE']
    listening_list   = ['Conversation01','SentenceStructure01','EnglishNews001','Medium01','Medium02',
                        'SimonReading_P1_01', 'SimonReading_P1_02']
    auto_list        = ['Conversation01','SentenceStructure01','Medium01','Medium02']
    verb_tense_01    = ['The rabbit eats carrots.'            ,'The rabbit ate a carrot.'            ,'The rabbit will eat a carrot.'             ,'I said the rabbit would eat a carrot.',
                        'The rabbit is eating a carrot.'      ,'The rabbit was eating a carrot.'     ,'The rabbit will be eating a carrot.'       ,'I said the rabbit would be eating a carrot.',
                        'The rabbit has eaten a carrot.'      ,'The rabbit had eaten a carrot.'      ,'The rabbit will have eaten a carrot.'      ,'I said the rabbit would have eaten a carrot.',
                        'The rabbit has been eating a carrot.','The rabbit had been eating a carrot.','The rabbit will have been eating a carrot.','I said the rabbit would have been eating a carrot.']
    verb_tense_02    = ['I do yoga.'             ,'I did yoga.'           ,'I will do yoga.'             ,'I said I would do yoga.',
                        'I am doing yoga.'       ,'I was doing yoga.'     ,'I will be doing yoga.'       ,'I said I would be doing yoga.',
                        'I have done yoga.'      ,'I had done yoga.'      ,'I will have done yoga.'      ,'I said I would have done yoga.',
                        'I have been doing yoga.','I had been doing yoga.','I will have been doing yoga.','I said I would have been doing yoga.']
    verb_tense       = verb_tense_02
    tts_mode         = ['en','cn']
    FORCE_SINGLE_M   = True
    SINGLE_MEAN      = False
    update_text_signal = pyqtSignal(str)  # 定义信号
    def __init__(self):
        super().__init__()
        self.generateAllWords = False
        self.netOK = False
        check_net = threading.Thread(target=self.fun_check_net)
        check_net.start()
        self.dictionary = PyDictionary()
        self.update_text_signal.connect(self.ui_update_text)
        self.translator = AutoTranslator(who='googletrans',src_lang='en',to_lang='zh-cn')
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
        self.EbbinghausTable  = EnglishPractice.vocabulary_list[0]
        self.writeEbbinghaus  = WriteEbbinghausDB("Ebbinghaus.db")
        self.writeEbbinghaus.createEbbinghausTable(self.EbbinghausTable)
        self.ebdb             = ReadEbbinghausDB("Ebbinghaus.db",self.EbbinghausTable)
        self.score            = 0
        self.ebbinghaus       = Ebbinghaus()
        self.sentenceCriteria = 0.9
        self.lastCurrent      = ''
        self.typeCnt          = 0
        self.wordModeLast     = self.wordMode
        # 听力相关变量
        self.links                 = []
        self.listeningSentences    = []
        self.listeningTranslations = []
        self.listenIndex           = 0
        self.listenCount           = self.db.getListenContent()
        self.listeningTable        = EnglishPractice.listening_list[0]
        # 从 UI 定义中动态 创建一个相应的窗口对象
        self.ui = uic.loadUi("ui/EnglishPractice.ui")
        self.radioButtonChanged    =    False
        self.ui.pushButton_7.setVisible(False)
        self.ui.pushButton_8.setVisible(False)
        self.ui.checkBox_3.setVisible(False)
        self.ui.checkBox_4.setVisible(False)
        self.ui.pushButton_21.setVisible(False)
        self.ui.pushButton_22.setVisible(False)
        self.ui.pushButton_23.setVisible(False)
        self.ui.pushButton_24.setVisible(False)
        self.ui.pushButton_25.setVisible(False)
        # 听力设置相关
        self.ui.label_10.setText(str(self.listenCount))
        # Settings 中的 Word 数据源选择
        self.ui.comboBox.addItems(self.wordTables)
        self.ui.comboBox.currentIndexChanged.connect(self.ui_wordSourceChanged)
        # Settings 中的 Listening 数据源选择
        self.ui.comboBox_2.addItems(self.listeningTables)
        self.ui.comboBox_2.currentIndexChanged.connect(self.ui_sentenceSourceChanged)
        # Settings 中 Auto 相关
        self.wav = WAV("wav")
        self.ui.groupBox_23.setVisible(False)
        self.autoSpeak             = False
        self.autoPlay              = False
        if WAV.VALID:
            self.autoTimer             = QTimer(self)
            self.autoTimerState        = False
            self.autoTimer.setSingleShot(True)
            self.autoTimer.timeout.connect(self.on_Timer)
            self.autoSpeak             = False
            self.autoPlay              = False
            self.repeat                = 0
            self.start_idx = int(self.ui.lineEdit_6.text()) - 1
            self.end_idx   = int(self.ui.lineEdit_7.text()) - 1
            self.autoSpeakIndex        = 0
            self.autoSpeakSentences    = []
            self.autoSpeakTranslations = []
            self.ui.comboBox_4.currentIndexChanged.connect(self.ui_autoSentenceSourceChanged)
            self.ui.lineEdit_6.textChanged.connect(self.ui_fromIndexChanged)
            self.ui.lineEdit_7.textChanged.connect(self.ui_toIndexChanged)
            self.ui.pushButton_29.clicked.connect(self.ui_dictationGoClicked)
            self.ui.pushButton_30.clicked.connect(self.ui_autoPlayClicked)
            self.ui.pushButton_31.clicked.connect(self.ui_autoPauseClicked)
            self.ui.comboBox_4.addItems(EnglishPractice.auto_list)
            self.ui.lineEdit_8.textChanged.connect(self.ui_calcExerciseDuration)
            self.fun_initAuto()
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
        self.ui.checkBox_5.toggled.connect(self.ui_oneMean)
        self.ui.lineEdit_11.textChanged.connect(self.ui_similarityChanged)
        self.ui.label_113.setVisible(False)
        self.ui.label_114.setVisible(False)
        self.ui.label_115.setVisible(False)
        self.ui.lineEdit_11.setVisible(False)
        # Marked Only
        self.ui.checkBox_4.toggled.connect(self.fun_markedOnly)
        # TTS
        self.ui.radioButton_4.clicked.connect(self.ui_ttsChineseSelected)
        self.ui.radioButton_5.clicked.connect(self.ui_ttsEnglishSelected)
        self.ttsMode = EnglishPractice.tts_mode[0]
        self.ui.lineEdit_4.textChanged.connect(self.tts_SpeedChange)
        self.ui.comboBox_3.currentIndexChanged.connect(self.tts_AccentChange)
        self.engine = pyttsx3.init()
        self.ignoreTTS = True
        self.tts_SpeedChange()
        self.tts_AccentChange()
        self.ui.pushButton_21.clicked.connect(self.ui_wordUKClicked)
        self.ui.pushButton_22.clicked.connect(self.ui_wordUSClicked)
        self.ui.pushButton_23.clicked.connect(self.ui_translationClicked)
        self.ui.pushButton_24.clicked.connect(self.ui_sentenceUSClicked)
        self.ui.pushButton_25.clicked.connect(self.ui_sentenceUKClicked)
        # 听力页面相关
        self.ui.pushButton_26.setVisible(False)
        self.ui.pushButton_27.setVisible(False)
        self.ui.pushButton_28.setVisible(False)
        self.ui.pushButton_26.clicked.connect(self.ui_listenUSClicked)
        self.ui.pushButton_27.clicked.connect(self.ui_listenUKClicked)
        self.ui.pushButton_28.clicked.connect(self.ui_listenTranslationClicked)
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
        self.ui.pushButton_9.clicked.connect(self.ui_vedioPausePaly)
        self.ui.pushButton_10.clicked.connect(self.ui_skipAd)
        self.ui.pushButton_11.clicked.connect(self.ui_openYoutube)
        self.ui.pushButton_12.clicked.connect(self.ui_againClicked)
        self.ui.pushButton_13.clicked.connect(self.ui_onceMoreClicked)
        self.ui.pushButton_14.clicked.connect(self.ui_back5sClicked)
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
        # Youtube 视频相关
        self.ytb = Youtube()
        # 时态相关
        self.ui.pushButton_15.clicked.connect(self.ui_clearVerbTense)
        self.ui.textEdit_6.textChanged.connect(self.ui_verbTense01Changed)
        self.ui.textEdit_7.textChanged.connect(self.ui_verbTense02Changed)
        self.ui.textEdit_8.textChanged.connect(self.ui_verbTense03Changed)
        self.ui.textEdit_9.textChanged.connect(self.ui_verbTense04Changed)
        self.ui.textEdit_10.textChanged.connect(self.ui_verbTense05Changed)
        self.ui.textEdit_11.textChanged.connect(self.ui_verbTense06Changed)
        self.ui.textEdit_12.textChanged.connect(self.ui_verbTense07Changed)
        self.ui.textEdit_13.textChanged.connect(self.ui_verbTense08Changed)
        self.ui.textEdit_14.textChanged.connect(self.ui_verbTense09Changed)
        self.ui.textEdit_15.textChanged.connect(self.ui_verbTense10Changed)
        self.ui.textEdit_16.textChanged.connect(self.ui_verbTense11Changed)
        self.ui.textEdit_17.textChanged.connect(self.ui_verbTense12Changed)
        self.ui.textEdit_18.textChanged.connect(self.ui_verbTense13Changed)
        self.ui.textEdit_19.textChanged.connect(self.ui_verbTense14Changed)
        self.ui.textEdit_20.textChanged.connect(self.ui_verbTense15Changed)
        self.ui.textEdit_21.textChanged.connect(self.ui_verbTense16Changed)
        # 语气相关
        self.ui.pushButton_16.clicked.connect(self.ui_page)
        self.ui.pushButton_17.clicked.connect(self.ui_page2)
        self.ui.pushButton_18.clicked.connect(self.ui_page3)
        self.ui.pushButton_19.clicked.connect(self.ui_page4)
        self.ui.pushButton_20.clicked.connect(self.ui_page5)
        self.ui.textEdit_22.textChanged.connect(self.ui_mood22)
        self.ui.textEdit_23.textChanged.connect(self.ui_mood23)
        self.ui.textEdit_24.textChanged.connect(self.ui_mood24)
        self.ui.textEdit_25.textChanged.connect(self.ui_mood25)
        self.ui.textEdit_26.textChanged.connect(self.ui_mood26)
        self.ui.textEdit_27.textChanged.connect(self.ui_mood27)
        self.ui.textEdit_28.textChanged.connect(self.ui_mood28)
        self.ui.textEdit_29.textChanged.connect(self.ui_mood29)
        self.ui.textEdit_30.textChanged.connect(self.ui_mood30)
        self.ui.textEdit_31.textChanged.connect(self.ui_mood31)
        self.ui.textEdit_32.textChanged.connect(self.ui_mood32)
        self.ui.textEdit_33.textChanged.connect(self.ui_mood33)
        self.ui.textEdit_34.textChanged.connect(self.ui_mood34)
        self.ui.textEdit_35.textChanged.connect(self.ui_mood35)
        self.ui.textEdit_36.textChanged.connect(self.ui_mood36)
        self.ui.textEdit_37.textChanged.connect(self.ui_mood37)
        self.ui.textEdit_38.textChanged.connect(self.ui_mood38)
        self.ui.textEdit_39.textChanged.connect(self.ui_mood39)
        self.ui.textEdit_40.textChanged.connect(self.ui_mood40)
        self.ui.textEdit_41.textChanged.connect(self.ui_mood41)
        self.ui.textEdit_42.textChanged.connect(self.ui_mood42)
        self.ui.textEdit_43.textChanged.connect(self.ui_mood43)
        self.ui.textEdit_44.textChanged.connect(self.ui_mood44)
        self.ui.textEdit_45.textChanged.connect(self.ui_mood45)
        self.ui.textEdit_46.textChanged.connect(self.ui_mood46)
        self.ui.textEdit_47.textChanged.connect(self.ui_mood47)
        self.ui.textEdit_48.textChanged.connect(self.ui_mood48)
        self.ui.textEdit_49.textChanged.connect(self.ui_mood49)
        self.ui.textEdit_50.textChanged.connect(self.ui_mood50)
        self.ui.textEdit_51.textChanged.connect(self.ui_mood51)
        self.ui.textEdit_52.textChanged.connect(self.ui_mood52)
        self.ui.textEdit_53.textChanged.connect(self.ui_mood53)
        self.ui.textEdit_54.textChanged.connect(self.ui_mood54)
        self.ui.textEdit_55.textChanged.connect(self.ui_mood55)
        self.ui.textEdit_56.textChanged.connect(self.ui_mood56)
        self.ui.textEdit_57.textChanged.connect(self.ui_mood57)
        self.ui.textEdit_58.textChanged.connect(self.ui_mood58)
        self.ui.textEdit_59.textChanged.connect(self.ui_mood59)
        self.ui.textEdit_60.textChanged.connect(self.ui_mood60)
        self.ui.textEdit_61.textChanged.connect(self.ui_mood61)
        self.ui.textEdit_62.textChanged.connect(self.ui_mood62)
        self.ui.textEdit_63.textChanged.connect(self.ui_mood63)
        self.ui.textEdit_64.textChanged.connect(self.ui_mood64)
        self.ui.textEdit_65.textChanged.connect(self.ui_mood65)
        self.ui.textEdit_66.textChanged.connect(self.ui_mood66)
        self.ui.textEdit_67.textChanged.connect(self.ui_mood67)
        self.ui.textEdit_69.textChanged.connect(self.ui_mood69)
        self.ui.textEdit_70.textChanged.connect(self.ui_mood70)
        self.ui.textEdit_71.textChanged.connect(self.ui_mood71)
        self.ui.textEdit_72.textChanged.connect(self.ui_mood72)
        self.ui.textEdit_73.textChanged.connect(self.ui_mood73)
        self.ui.textEdit_74.textChanged.connect(self.ui_mood74)
    def fun_check_net(self):
        if self.fun_connect_to_youtube():
            self.netOK = True
        else:
            self.netOK = False
        if self.netOK:
            self.ui.textBrowser_3.setVisible(True)
            en_dict = threading.Thread(target=self.fun_online_dictionary,args=(self.currentWord,))
            en_dict.start()
            cn_dict = threading.Thread(target=self.fun_online_translate,args=(self.currentWord,))
            cn_dict.start()
        else:
            self.ui.textBrowser_3.setVisible(False)
                
    def fun_safe_translate(self,translator, sentence, max_attempts=3):
        attempt = 0
        while attempt < max_attempts:
            try:
                # 尝试执行翻译操作
                translation = translator.trans(sentence)
                return translation  # 如果成功，返回翻译结果
            except Exception as e:  # 捕获所有异常
                print(f"Attempt {attempt + 1} failed with error: {e}")
                attempt += 1  # 增加尝试次数
        return None
    def fun_connect_to_youtube(self):
        try:
            # 尝试请求YouTube的主页
            response = requests.get('https://www.youtube.com', timeout=3)
            # 如果响应状态码为200，返回True
            if response.status_code == 200:
                return True
            else:
                return False
        except requests.RequestException:
            # 如果请求过程中发生异常（如连接错误、超时等），返回False
            return False
    def ui_oneMean(self):
        EnglishPractice.FORCE_SINGLE_M = self.ui.checkBox_5.isChecked()
        if EnglishPractice.FORCE_SINGLE_M:
            EnglishPractice.SINGLE_MEAN = True
        else:
            EnglishPractice.SINGLE_MEAN = False
        self.wordIndex = 0
        self.p_list    = []
        self.f_generateWords()
        self.ui_renewUI()
        self.f_writeConfigFile()
    def ui_clearStackedWidget(self):
        self.ui.textEdit_22.clear()
        self.ui.textEdit_23.clear()
        self.ui.textEdit_24.clear()
        self.ui.textEdit_25.clear()
        self.ui.textEdit_26.clear()
        self.ui.textEdit_27.clear()
        self.ui.textEdit_28.clear()
        self.ui.textEdit_29.clear()
        self.ui.textEdit_30.clear()
        self.ui.textEdit_31.clear()
        self.ui.textEdit_32.clear()
        self.ui.textEdit_33.clear()
        self.ui.textEdit_34.clear()
        self.ui.textEdit_35.clear()
        self.ui.textEdit_36.clear()
        self.ui.textEdit_37.clear()
        self.ui.textEdit_38.clear()
        self.ui.textEdit_39.clear()
        self.ui.textEdit_40.clear()
        self.ui.textEdit_41.clear()
        self.ui.textEdit_42.clear()
        self.ui.textEdit_43.clear()
        self.ui.textEdit_44.clear()
        self.ui.textEdit_45.clear()
        self.ui.textEdit_46.clear()
        self.ui.textEdit_47.clear()
        self.ui.textEdit_48.clear()
        self.ui.textEdit_49.clear()
        self.ui.textEdit_50.clear()
        self.ui.textEdit_51.clear()
        self.ui.textEdit_52.clear()
        self.ui.textEdit_53.clear()
        self.ui.textEdit_54.clear()
        self.ui.textEdit_55.clear()
        self.ui.textEdit_56.clear()
        self.ui.textEdit_57.clear()
        self.ui.textEdit_58.clear()
        self.ui.textEdit_59.clear()
        self.ui.textEdit_60.clear()
        self.ui.textEdit_61.clear()
        self.ui.textEdit_62.clear()
        self.ui.textEdit_63.clear()
        self.ui.textEdit_64.clear()
        self.ui.textEdit_65.clear()
        self.ui.textEdit_66.clear()
        self.ui.textEdit_67.clear()
        self.ui.textEdit_69.clear()
        self.ui.textEdit_70.clear()
        self.ui.textEdit_71.clear()
        self.ui.textEdit_72.clear()
        self.ui.textEdit_73.clear()
        self.ui.textEdit_74.clear()
    def ui_page(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page)
        self.ui_clearStackedWidget()
    def ui_page2(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_2)
        self.ui_clearStackedWidget()
    def ui_page3(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_3)
        self.ui_clearStackedWidget()
    def ui_page4(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_4)
        self.ui_clearStackedWidget()
    def ui_page5(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_5)
        self.ui_clearStackedWidget()
    def ui_focusNextEdit(self,who,Text,nextEdit):
        nextEdit.setFocus()
        who.setText(Text)
    def ui_mood22(self):
        who      = self.ui.textEdit_22
        sentence = MoodText.Text22
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_23)
    def ui_mood23(self):
        who      = self.ui.textEdit_23
        sentence = MoodText.Text23
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_24)
    def ui_mood24(self):
        who      = self.ui.textEdit_24
        sentence = MoodText.Text24
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_25)
    def ui_mood25(self):
        who      = self.ui.textEdit_25
        sentence = MoodText.Text25
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_26)
    def ui_mood26(self):
        who      = self.ui.textEdit_26
        sentence = MoodText.Text26
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_27)
    def ui_mood27(self):
        who      = self.ui.textEdit_27
        sentence = MoodText.Text27
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_28)
    def ui_mood28(self):
        who      = self.ui.textEdit_28
        sentence = MoodText.Text28
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_29)
    def ui_mood29(self):
        who      = self.ui.textEdit_29
        sentence = MoodText.Text29
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_30)
    def ui_mood30(self):
        who      = self.ui.textEdit_30
        sentence = MoodText.Text30
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_30)
    def ui_mood33(self):
        who      = self.ui.textEdit_33
        sentence = MoodText.Text33
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_36)
    def ui_mood36(self):
        who      = self.ui.textEdit_36
        sentence = MoodText.Text36
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_34)
    def ui_mood34(self):
        who      = self.ui.textEdit_34
        sentence = MoodText.Text34
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_35)
    def ui_mood35(self):
        who      = self.ui.textEdit_35
        sentence = MoodText.Text35
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_31)
    def ui_mood31(self):
        who      = self.ui.textEdit_31
        sentence = MoodText.Text31
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_32)
    def ui_mood32(self):
        who      = self.ui.textEdit_32
        sentence = MoodText.Text32
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_37)
    def ui_mood37(self):
        who      = self.ui.textEdit_37
        sentence = MoodText.Text37
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_37)
    def ui_mood38(self):
        who      = self.ui.textEdit_38
        sentence = MoodText.Text38
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_42)
    def ui_mood42(self):
        who      = self.ui.textEdit_42
        sentence = MoodText.Text42
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_39)
    def ui_mood39(self):
        who      = self.ui.textEdit_39
        sentence = MoodText.Text39
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_40)
    def ui_mood40(self):
        who      = self.ui.textEdit_40
        sentence = MoodText.Text40
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_41)
    def ui_mood41(self):
        who      = self.ui.textEdit_41
        sentence = MoodText.Text41
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_43)
    def ui_mood43(self):
        who      = self.ui.textEdit_43
        sentence = MoodText.Text43
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_44)
    def ui_mood44(self):
        who      = self.ui.textEdit_44
        sentence = MoodText.Text44
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_45)
    def ui_mood45(self):
        who      = self.ui.textEdit_45
        sentence = MoodText.Text45
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_45)
    def ui_mood46(self):
        who      = self.ui.textEdit_46
        sentence = MoodText.Text46
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_47)
    def ui_mood47(self):
        who      = self.ui.textEdit_47
        sentence = MoodText.Text47
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_48)
    def ui_mood48(self):
        who      = self.ui.textEdit_48
        sentence = MoodText.Text48
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_49)
    def ui_mood49(self):
        who      = self.ui.textEdit_49
        sentence = MoodText.Text49
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_50)
    def ui_mood50(self):
        who      = self.ui.textEdit_50
        sentence = MoodText.Text50
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_51)
    def ui_mood51(self):
        who      = self.ui.textEdit_51
        sentence = MoodText.Text51
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_51)
    def ui_mood52(self):
        who      = self.ui.textEdit_52
        sentence = MoodText.Text52
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_58)
    def ui_mood58(self):
        who      = self.ui.textEdit_58
        sentence = MoodText.Text58
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_53)
    def ui_mood53(self):
        who      = self.ui.textEdit_53
        sentence = MoodText.Text53
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_54)
    def ui_mood54(self):
        who      = self.ui.textEdit_54
        sentence = MoodText.Text54
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_55)
    def ui_mood55(self):
        who      = self.ui.textEdit_55
        sentence = MoodText.Text55_a
        input_sentence = who.toPlainText()
        if not self.ui_verbTenseDiff(who, input_sentence, sentence):
            sentence = MoodText.Text55_b
            self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_56)
    def ui_mood56(self):
        who      = self.ui.textEdit_56
        sentence = MoodText.Text56
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_56)
    def ui_mood57(self):
        who      = self.ui.textEdit_57
        sentence = MoodText.Text57
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_60)
    def ui_mood60(self):
        who      = self.ui.textEdit_60
        sentence = MoodText.Text60
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_61)
    def ui_mood61(self):
        who      = self.ui.textEdit_61
        sentence = MoodText.Text61
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_62)
    def ui_mood62(self):
        who      = self.ui.textEdit_62
        sentence = MoodText.Text62_a
        input_sentence = who.toPlainText()
        if not self.ui_verbTenseDiff(who, input_sentence, sentence):
            sentence = MoodText.Text62_b
            self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_62)
    def ui_mood59(self):
        who      = self.ui.textEdit_59
        sentence = MoodText.Text59
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_64)
    def ui_mood64(self):
        who      = self.ui.textEdit_64
        sentence = MoodText.Text64
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_63)
    def ui_mood63(self):
        who      = self.ui.textEdit_63
        sentence = MoodText.Text63_a
        input_sentence = who.toPlainText()
        if not self.ui_verbTenseDiff(who, input_sentence, sentence):
            sentence = MoodText.Text63_b
            if not self.ui_verbTenseDiff(who, input_sentence, sentence):
                sentence = MoodText.Text63_c
                if not self.ui_verbTenseDiff(who, input_sentence, sentence):
                    sentence = MoodText.Text63_d
                    self.ui_verbTenseDiff(who, input_sentence, sentence)        
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_65)
    def ui_mood65(self):
        who      = self.ui.textEdit_65
        sentence = MoodText.Text65_a
        input_sentence = who.toPlainText()
        if not self.ui_verbTenseDiff(who, input_sentence, sentence):
            sentence = MoodText.Text65_b
            if not self.ui_verbTenseDiff(who, input_sentence, sentence):
                sentence = MoodText.Text65_c
                if not self.ui_verbTenseDiff(who, input_sentence, sentence):
                    sentence = MoodText.Text65_d
                    self.ui_verbTenseDiff(who, input_sentence, sentence)        
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_66)
    def ui_mood66(self):
        who      = self.ui.textEdit_66
        sentence = MoodText.Text66
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_67)
    def ui_mood67(self):
        who      = self.ui.textEdit_67
        sentence = MoodText.Text67
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_69)
    def ui_mood69(self):
        who      = self.ui.textEdit_69
        sentence = MoodText.Text69
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_69)
    def ui_mood70(self):
        who      = self.ui.textEdit_70
        sentence = MoodText.Text70
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_70)
    def ui_mood71(self):
        who      = self.ui.textEdit_71
        sentence = MoodText.Text71
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_72)
    def ui_mood72(self):
        who      = self.ui.textEdit_72
        sentence = MoodText.Text72
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_72)
    def ui_mood73(self):
        who      = self.ui.textEdit_73
        sentence = MoodText.Text73
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_73)
    def ui_mood74(self):
        who      = self.ui.textEdit_74
        sentence = MoodText.Text74
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_74)
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

    def ui_ttsChineseSelected(self):
        self.ui.label_23.setVisible(False)
        self.ui.comboBox_3.setVisible(False)
        self.ttsMode = EnglishPractice.tts_mode[1]
        if not EnglishPractice.FORCE_SINGLE_M:
            EnglishPractice.SINGLE_MEAN = True
    def ui_ttsEnglishSelected(self):
        self.ui.label_23.setVisible(True)
        self.ui.comboBox_3.setVisible(True)
        self.ttsMode = EnglishPractice.tts_mode[0]
        self.tts_SpeedChange()
        self.tts_AccentChange()
        if not EnglishPractice.FORCE_SINGLE_M:
            EnglishPractice.SINGLE_MEAN = False
    def tts_SpeedChange(self):
        self.ttsSpeed = int(self.ui.lineEdit_4.text().strip()) if len(self.ui.lineEdit_4.text().strip()) > 0 else 120
        self.engine.setProperty('rate', self.ttsSpeed)
        if self.ignoreTTS:
            return
        else:
            self.f_writeConfigFile()
    def tts_AccentChange(self):
        # Auto
        if WAV.VALID:
            self.fun_calcDuration()
        # Get current accent
        self.ttsAccent = self.ui.comboBox_3.currentText().lower()
        # Get available voices and set to English
        voices = self.engine.getProperty('voices')
        selected_voice = None
        for voice in voices:
            if 'english' in voice.name.lower():  # Check if the voice is English
                selected_voice = voice.id
        for voice in voices:
            if self.ttsAccent == 'american' and 'en-us' in voice.id.lower():  # American English
                selected_voice = voice.id
                break
            elif self.ttsAccent == 'british' and 'en-gb' in voice.id.lower():  # British English
                selected_voice = voice.id
                break
        # Set the voice
        if selected_voice:
            self.engine.setProperty('voice', selected_voice)
        else:
            print(f"No {self.ttsAccent} accent voice found. Using default voice.")
        if self.ignoreTTS:
            return
        else:
            self.f_writeConfigFile()

    def speak_cn(self, content):
        def run_speak():
            # Say the word
            try:
                self.engine.setProperty('rate', 250)
                voices = self.engine.getProperty('voices')
                selected_voice = None
                for voice in voices:
                    if 'chinese' in voice.name.lower():  # Check if the voice is English
                        selected_voice = voice.id
                if selected_voice:
                    self.engine.setProperty('voice', selected_voice)
                else:
                    print(f"No {self.ttsAccent} accent voice found. Using default voice.")
                self.engine.say(content)
                self.engine.runAndWait()
            except (RuntimeError) as e:
                pass
        # Create and start the thread
        speak_thread = threading.Thread(target=run_speak)
        speak_thread.start()        
    def speak(self, content, cn_str=""):
        def run_speak():
            # Say the word
            try:
                self.engine.say(content)
                self.engine.runAndWait()
                wav_file = "wav/"+self.EbbinghausTable+"/words_cn/"+cn_str+".wav"
                if self.f_check_file(wav_file):
                    self.fun_play_wav(wav_file)
            except (RuntimeError) as e:
                pass
        # Create and start the thread
        speak_thread = threading.Thread(target=run_speak)
        speak_thread.start()
        
    def fun_initWithConfig(self):
        self.useSentenceScore = False
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
        self.ui.comboBox.setCurrentText(self.configDict.get("Source"))
        self.ui_wordSourceChanged()
        self.ui.checkBox_5.setChecked(self.configDict.get("OneMean"))
        # 听力设置恢复
        self.listeningTable = self.configDict.get("Source2")
        self.listenCount    = self.db.getListenContent(self.listeningTable)
        self.ui.label_10.setText(str(self.listenCount))
        self.ui.comboBox_2.setCurrentText(self.listeningTable)
        self.ui.lineEdit_2.setText(str(self.configDict.get("From")))
        self.ui.lineEdit_3.setText(str(self.configDict.get("To")))
        self.ui.progressBar_2.setMinimum(int(self.ui.lineEdit_2.text().strip()))
        self.ui.progressBar_2.setMaximum(int(self.ui.lineEdit_3.text().strip()))
        self.listenPracticeCnt = int(self.ui.lineEdit_3.text().strip()) - int(self.ui.lineEdit_2.text().strip())
        self.idxListen = int(self.ui.lineEdit_2.text().strip()) - 1
        self.currentListening = self.db.getListenSentence(self.idxListen)
        # TTS 设置恢复
        self.ui.lineEdit_4.setText(str(self.configDict.get("Speed")))
        self.ui.comboBox_3.setCurrentText(self.configDict.get("Accent"))

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
                                "To":int(self.ui.lineEdit_3.text().strip()) if len(self.ui.lineEdit_3.text().strip()) > 0 else 2,
                                "Speed":int(self.ui.lineEdit_4.text().strip()) if len(self.ui.lineEdit_4.text().strip()) > 0 else 120,
                                "Accent":self.ui.comboBox_3.currentText(),
                                "OneMean":self.ui.checkBox_5.isChecked()
                                }
            #json.dump(self.configDict,file)
            file.write(json.dumps(self.configDict,ensure_ascii=False,indent=2))

    def fun_updateMarked(self):
        # Marked 的钩选状态
        if self.wordMode == 2 or self.updateInReview:
            self.ebWords = self.ebdb.getWords(self.EbbinghausTable,self.useSentenceScore)
            if self.ebdb.getMarked(self.currentWord) is not None:
                self.ui.checkBox_3.setChecked(int(self.ebdb.getMarked(self.currentWord)))
            else:
                self.ui.checkBox_3.setChecked(False)

    def ui_renewUI(self,getNewWords = True):
        self.wordIndex        = 0
        self.words_p_lines    = ''
        self.score            = 0
        if getNewWords:
            self.fun_getNewWords()
        # 初始化界面上的文字信息
        self.ui_setWordFromIndex(self.wordIndex)
        self.ui.textEdit.clear()
        self.ui.textEdit_2.clear()
        self.ui.textEdit_3.clear()
        if self.netOK:
            self.ui.textBrowser_3.clear()
        # 是否显示 Once more
        if self.practiceMode == EnglishPractice.practiceModeList[1]:
            self.ui.pushButton_13.setVisible(True)
        else:
            self.ui.pushButton_13.setVisible(False)
        self.fun_updateMarked()

    def ui_selectEbbinghaus(self):
        self.ui.label_113.setVisible(False)
        self.ui.label_114.setVisible(False)
        self.ui.label_115.setVisible(False)
        self.ui.lineEdit_11.setVisible(False)
        self.ui.checkBox.setVisible(True)
        self.ui.checkBox.setEnabled(True)
        self.ui.checkBox_3.setVisible(True)
        self.ui.checkBox_4.setVisible(True)
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
        self.ui_wordSourceChanged()
        if self.ui.radioButton.isChecked():
            self.f_writeConfigFile()

    def ui_onGoClicked(self):
        if WAV.VALID:
            self.autoTimer.stop()
            self.autoTimerState = False
        self.ui.pushButton_31.setVisible(False)
        self.ui_setAutoPlayVisible(True)
        self.autoSpeak = False
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
        self.f_writeConfigFile()
        self.ui_onListeningPageChanged()
        self.ui_listenTTSVisible()
        
        # Yutube 视频相关
        self.ytb.open_link(self.db.getListenLink(self.idxListen))

    def ui_listenTTSVisible(self):
        import re
        def sanitize_filename(filename):
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        self.ui.pushButton_26.setVisible(False)
        self.ui.pushButton_27.setVisible(False)
        self.ui.pushButton_28.setVisible(False)
        sentence_file = sanitize_filename(self.currentListening)
        if self.autoSpeak == True:
            sentence_file = sanitize_filename(self.autoSpeakSentences[self.autoSpeakIndex])
            folder_selector = self.ui.comboBox_3.currentText().strip().lower()
            if folder_selector == 'american':
                file_path = self.auto_file_path + "/listen_us"
            elif folder_selector == 'british':
                file_path = self.auto_file_path + "/listen_uk"
            wav_file = file_path+"/"+sentence_file+".wav"
            if self.f_check_file(wav_file):
                if not self.autoPlay:
                    self.ui.pushButton_26.setVisible(True)
                else:
                    self.ui.pushButton_26.setVisible(False)
            if self.f_check_file(wav_file):
                if not self.autoPlay:
                    self.ui.pushButton_27.setVisible(True)
                else:
                    self.ui.pushButton_27.setVisible(False)
            translation_file = sanitize_filename(self.autoSpeakTranslations[self.autoSpeakIndex])
            if self.f_check_file(self.auto_file_path+"/translations/"+translation_file+".wav"):
                if not self.autoPlay:
                    self.ui.pushButton_28.setVisible(True)
                else:
                    self.ui.pushButton_28.setVisible(False)
        else:
            if self.f_check_file("wav/"+self.listeningTable+"/listen_us/"+sentence_file+".wav"):
                self.ui.pushButton_26.setVisible(True)
            if self.f_check_file("wav/"+self.listeningTable+"/listen_uk/"+sentence_file+".wav"):
                self.ui.pushButton_27.setVisible(True)
            translation_file = sanitize_filename(self.db.getListenTranslation(self.idxListen))
            if self.f_check_file("wav/"+self.listeningTable+"/translations/"+translation_file+".wav"):
                self.ui.pushButton_28.setVisible(True)

    def ui_listenUSClicked(self):
        import re
        def sanitize_filename(filename):
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        sentence_file = sanitize_filename(self.currentListening)
        if self.autoSpeak:
            wav_file = self.auto_file_path+"/listen_us/"+sentence_file+".wav"
        else:
            wav_file = "wav/"+self.listeningTable+"/listen_us/"+sentence_file+".wav"
        self.fun_play_wav(wav_file)
    def ui_listenUKClicked(self):
        import re
        def sanitize_filename(filename):
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        sentence_file = sanitize_filename(self.currentListening)
        if self.autoSpeak:
            wav_file = self.auto_file_path+"/listen_uk/"+sentence_file+".wav"
        else:
            wav_file = "wav/"+self.listeningTable+"/listen_uk/"+sentence_file+".wav"
        self.fun_play_wav(wav_file)
    def ui_listenTranslationClicked(self):
        import re
        def sanitize_filename(filename):
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        if self.autoSpeak:
            sentence_file = sanitize_filename(self.autoSpeakTranslations[self.autoSpeakIndex])
            wav_file = self.auto_file_path+"/translations/"+sentence_file+".wav"
        else:
            sentence_file = sanitize_filename(self.db.getListenTranslation(self.idxListen))
            wav_file = "wav/"+self.listeningTable+"/translations/"+sentence_file+".wav"
        self.fun_play_wav(wav_file)

    def ui_onSentencePrevClicked(self):
        self.ui.textEdit_4.clear()
        self.ui_listenTTSVisible()
        if self.autoSpeak:
            if self.autoSpeakIndex > 0:
                self.autoSpeakIndex -= 1
                self.currentListening = self.autoSpeakSentences[self.autoSpeakIndex]
                if len(self.user_inputs[self.autoSpeakIndex]) > 0:
                    self.ui.textEdit_4.textCursor().insertText(self.user_inputs[self.autoSpeakIndex])
                self.ui.progressBar_2.setValue(self.autoSpeakIndex)
                self.ui.textBrowser_2.setText(self.autoSpeakTranslations[self.autoSpeakIndex])
        else:
            if self.listenIndex > 0:
                self.listenIndex -= 1
                self.idxListen   -= 1
                self.currentListening = self.db.getListenSentence(self.idxListen)
            if len(self.user_inputs[self.idxListen]) > 0:
                self.ui.textEdit_4.textCursor().insertText(self.user_inputs[self.idxListen])
            self.ui.progressBar_2.setValue(self.idxListen+1)
            self.ui.textBrowser_2.setText(self.db.getListenTranslation(self.idxListen))

    def ui_onSentenceNextClicked(self):
        if self.autoSpeak:
            self.user_inputs[self.autoSpeakIndex] = self.input_listening.strip()
            if self.autoSpeakIndex < self.end_idx-self.start_idx:
                self.autoSpeakIndex += 1
                self.ui.progressBar_2.setValue(self.autoSpeakIndex)
                self.currentListening = self.autoSpeakSentences[self.autoSpeakIndex]
                if self.user_inputs.get(self.autoSpeakIndex) is not None:
                    if len(self.user_inputs[self.autoSpeakIndex]) > 0:
                        self.ui.textEdit_4.textCursor().insertText(self.user_inputs[self.autoSpeakIndex])
                self.ui.progressBar_2.setValue(self.autoSpeakIndex)
                if not self.autoPlay:
                    self.ui.textBrowser_2.setText(self.autoSpeakTranslations[self.autoSpeakIndex])
                    def sanitize_filename(filename):
                        import re
                        sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
                        return sanitized
                    sentence_file = sanitize_filename(self.autoSpeakSentences[self.autoSpeakIndex])
                    folder_selector = self.ui.comboBox_3.currentText().strip().lower()
                    if folder_selector == 'american':
                        file_path = self.auto_file_path + "/listen_us"
                    elif folder_selector == 'british':
                        file_path = self.auto_file_path + "/listen_uk"
                    wav_file = file_path+"/"+sentence_file+".wav"
                    self.fun_play_wav(wav_file)
        else:
            self.user_inputs[self.idxListen] = self.input_listening.strip()
            if self.listenIndex < self.listenPracticeCnt:
                self.listenIndex += 1
                self.idxListen   += 1
                self.currentListening = self.db.getListenSentence(self.idxListen)
                if self.user_inputs.get(self.idxListen) is not None:
                    if len(self.user_inputs[self.idxListen]) > 0:
                        self.ui.textEdit_4.textCursor().insertText(self.user_inputs[self.idxListen])
            self.ui.progressBar_2.setValue(self.idxListen+1)
            self.ui.textBrowser_2.setText(self.db.getListenTranslation(self.idxListen))
        self.ui.textEdit_4.clear()
        self.ui_listenTTSVisible()

    def on_Timer(self):
        def sanitize_filename(filename):
            import re
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        def play_en(sentence_en):
            sentence_file = sanitize_filename(sentence_en)
            folder_selector = self.ui.comboBox_3.currentText().strip().lower()
            if folder_selector == 'american':
                file_path = self.auto_file_path + "/listen_us"
            elif folder_selector == 'british':
                file_path = self.auto_file_path + "/listen_uk"
            wav_file = file_path+"/"+sentence_file+".wav"
            delay_ms = int(self.wav.duration(wav_file) * 1000) * 2
            repeat_count = int(self.ui.lineEdit_8.text())
            self.repeat += 1
            if self.repeat < repeat_count+1:
                self.fun_play_wav(wav_file)
            else:
                delay_ms = 10
                if self.autoSpeakIndex == self.end_idx-self.start_idx:
                    self.autoPlay = False
            if self.repeat == repeat_count+1:
                self.repeat = 0
                self.ui_onSentenceNextClicked()
                self.ui.textBrowser_2.clear()
            if self.autoPlay:
                self.autoTimer.start(delay_ms)
                self.autoTimerState = True
        play_en(self.autoSpeakSentences[self.autoSpeakIndex])

        show_en_idx  = int(self.ui.lineEdit_9.text())
        show_cn_idx  = int(self.ui.lineEdit_10.text())

        if self.repeat == show_en_idx:
            self.ui.textEdit_4.textCursor().insertText(self.autoSpeakSentences[self.autoSpeakIndex])
        if self.repeat == show_cn_idx:
            self.ui.textBrowser_2.setText(self.autoSpeakTranslations[self.autoSpeakIndex])        

    def ui_setAutoPlayVisible(self, visible):
        self.ui.pushButton_5.setVisible(visible)
        self.ui.pushButton_6.setVisible(visible)
        self.ui.pushButton_9.setVisible(visible)
        self.ui.pushButton_10.setVisible(visible)
        self.ui.pushButton_12.setVisible(visible)
        self.ui.pushButton_14.setVisible(visible)
        self.ui.textEdit_5.setVisible(visible)

    def ui_setDictationVisible(self, visible):
        self.ui.pushButton_9.setVisible(visible)
        self.ui.pushButton_10.setVisible(visible)
        self.ui.pushButton_12.setVisible(visible)
        self.ui.pushButton_14.setVisible(visible)

    def ui_autoPauseClicked(self):
        if self.autoTimerState:
            self.autoTimer.stop()
            self.autoTimerState = False
            self.ui.pushButton_31.setStyleSheet("QPushButton { background-color: red; }")
        else:
            self.autoTimer.start(1000)
            self.autoTimerState = True
            self.ui.pushButton_31.setStyleSheet("")
        
    def ui_autoPlayClicked(self):
        self.ui.pushButton_31.setVisible(True)
        self.ui_setAutoPlayVisible(False)
        self.autoSpeak = True
        self.autoPlay  = True
        self.repeat    = 0
        self.user_inputs = {}
        self.idxListen   = int(self.ui.lineEdit_6.text().strip()) - 1
        self.ui.progressBar_2.setMinimum(0)
        self.ui.progressBar_2.setMaximum(int(self.ui.lineEdit_7.text().strip())-int(self.ui.lineEdit_6.text().strip()))
        self.ui.progressBar_2.setValue(0)
        self.listenPracticeCnt = int(self.ui.lineEdit_7.text().strip()) - int(self.ui.lineEdit_6.text().strip())
        self.fun_calcDuration()
        self.ui.progressBar_2.setValue(self.autoSpeakIndex)
        self.ui.textBrowser_2.clear()
        self.ui.textEdit_4.clear()
        self.ui.tabWidget.setCurrentIndex(1)
        self.ui.textEdit_4.setFocus()
        self.currentListening = self.autoSpeakSentences[self.autoSpeakIndex]
        self.ui_onListeningPageChanged()
        self.ui_listenTTSVisible()
        self.autoTimer.start(1000)
        self.autoTimerState = True

    def ui_dictationGoClicked(self):
        self.autoTimer.stop()
        self.autoTimerState = False
        self.ui.pushButton_31.setVisible(False)
        self.ui_setAutoPlayVisible(True)
        self.ui_setDictationVisible(False)
        self.autoSpeak = True
        self.autoPlay  = False
        self.user_inputs = {}
        self.idxListen   = int(self.ui.lineEdit_6.text().strip()) - 1
        self.ui.progressBar_2.setMinimum(0)
        self.ui.progressBar_2.setMaximum(int(self.ui.lineEdit_7.text().strip())-int(self.ui.lineEdit_6.text().strip()))
        self.ui.progressBar_2.setValue(0)
        self.listenPracticeCnt = int(self.ui.lineEdit_7.text().strip()) - int(self.ui.lineEdit_6.text().strip())
        self.fun_calcDuration()
        self.ui.progressBar_2.setValue(self.autoSpeakIndex)
        self.ui.textBrowser_2.setText(self.autoSpeakTranslations[self.autoSpeakIndex])
        self.ui.textEdit_4.clear()
        self.ui.tabWidget.setCurrentIndex(1)
        self.ui.textEdit_4.setFocus()
        self.currentListening = self.autoSpeakSentences[self.autoSpeakIndex]
        self.ui_onListeningPageChanged()
        self.ui_listenTTSVisible()

        def sanitize_filename(filename):
            import re
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        sentence_file = sanitize_filename(self.autoSpeakSentences[self.autoSpeakIndex])
        folder_selector = self.ui.comboBox_3.currentText().strip().lower()
        if folder_selector == 'american':
            file_path = self.auto_file_path + "/listen_us"
        elif folder_selector == 'british':
            file_path = self.auto_file_path + "/listen_uk"
        wav_file = file_path+"/"+sentence_file+".wav"
        self.fun_play_wav(wav_file)

    def ui_fromIndexChanged(self):
        self.fun_calcDuration()
    def ui_toIndexChanged(self):
        self.fun_calcDuration()
    def fun_calcDuration(self):
        def sanitize_filename(filename):
            import re
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        duration_s = 0
        exercise_s = 0
        folder_selector = self.ui.comboBox_3.currentText().strip().lower()
        if folder_selector == 'american':
            file_path = self.auto_file_path + "/listen_us"
        elif folder_selector == 'british':
            file_path = self.auto_file_path + "/listen_uk"
        
        self.start_idx = int(self.ui.lineEdit_6.text() if len(self.ui.lineEdit_6.text()) > 0 else 1) - 1
        self.end_idx   = int(self.ui.lineEdit_7.text() if len(self.ui.lineEdit_7.text()) > 0 else 1) - 1
        if self.start_idx >=0 and self.start_idx <= self.end_idx:
            self.db.getListenContent(self.ui.comboBox_4.currentText())
            if self.ui.progressBar_2.value() == 0:
                self.autoSpeakIndex    = 0
            self.autoSpeakSentences    = []
            self.autoSpeakTranslations = []
            for idx in range(self.start_idx, self.end_idx + 1):
                self.autoSpeakSentences.append(self.db.getListenSentence(idx))
                self.autoSpeakTranslations.append(self.db.getListenTranslation(idx))
                file_name = sanitize_filename(self.db.getListenSentence(idx))+".wav"
                file_s = self.wav.duration(file_path+"/"+file_name)
                duration_s += file_s
                exercise_s += (file_s * 2 * int(self.ui.lineEdit_8.text() if len(self.ui.lineEdit_8.text()) > 0 else 1) + 0.01)
            self.ui.label_106.setText(self.wav.seconds_to_hms(duration_s))
            self.ui.label_112.setText(self.wav.seconds_to_hms(exercise_s))
    def ui_calcExerciseDuration(self):
        self.fun_calcDuration()
    def ui_autoSentenceSourceChanged(self):
        self.fun_initAuto()
    def fun_initAuto(self):
        if WAV.VALID:
            self.ui.groupBox_23.setVisible(True)
            self.auto_file_path = "wav/" + self.ui.comboBox_4.currentText()
            file_path = self.auto_file_path + "/translations"
            self.countNum = self.wav.count_wav_files(file_path)
            self.ui.label_101.setText(str(self.countNum))
            self.ui.lineEdit_7.setText(str(self.countNum))
        else:
            self.ui.groupBox_23.setVisible(False)
    
    def fun_initListening(self):
        if len(self.ui.lineEdit_2.text().strip()) > 0:
            self.idxListen = int(self.ui.lineEdit_2.text().strip()) - 1
            self.currentListening = self.db.getListenSentence(self.idxListen)
            self.ui.textBrowser_2.setText(self.db.getListenTranslation(self.idxListen))
            self.user_inputs = {}
            self.ui_listenTTSVisible()
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

    def ui_verbTenseDiff(self,who,input_sentence, sentence):
        res = False
        import difflib
        scoreVerbTense = difflib.SequenceMatcher(None, input_sentence.strip(), sentence.strip()).quick_ratio()
        if len(input_sentence) == 0:
            who.setStyleSheet("background:white")
            res = False
        elif int(scoreVerbTense) == 1:
            who.setStyleSheet("background:palegreen")
            res = True
        else:
            who.setStyleSheet("background:lavenderblush")
            res = False
        return res
    def ui_clearVerbTense(self):
        self.ui.textEdit_6.clear()
        self.ui.textEdit_7.clear()
        self.ui.textEdit_8.clear()
        self.ui.textEdit_9.clear()
        self.ui.textEdit_10.clear()
        self.ui.textEdit_11.clear()
        self.ui.textEdit_12.clear()
        self.ui.textEdit_13.clear()
        self.ui.textEdit_14.clear()
        self.ui.textEdit_15.clear()
        self.ui.textEdit_16.clear()
        self.ui.textEdit_17.clear()
        self.ui.textEdit_18.clear()
        self.ui.textEdit_19.clear()
        self.ui.textEdit_20.clear()
        self.ui.textEdit_21.clear()
    def ui_verbTense01Changed(self):
        who      = self.ui.textEdit_6
        sentence = EnglishPractice.verb_tense[0]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_7)
    def ui_verbTense02Changed(self):
        who      = self.ui.textEdit_7
        sentence = EnglishPractice.verb_tense[1]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_8)
    def ui_verbTense03Changed(self):
        who      = self.ui.textEdit_8
        sentence = EnglishPractice.verb_tense[2]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_9)
    def ui_verbTense04Changed(self):
        who      = self.ui.textEdit_9
        sentence = EnglishPractice.verb_tense[3]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_10)
    def ui_verbTense05Changed(self):
        who      = self.ui.textEdit_10
        sentence = EnglishPractice.verb_tense[4]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_11)
    def ui_verbTense06Changed(self):
        who      = self.ui.textEdit_11
        sentence = EnglishPractice.verb_tense[5]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_12)
    def ui_verbTense07Changed(self):
        who      = self.ui.textEdit_12
        sentence = EnglishPractice.verb_tense[6]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_13)
    def ui_verbTense08Changed(self):
        who      = self.ui.textEdit_13
        sentence = EnglishPractice.verb_tense[7]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_14)
    def ui_verbTense09Changed(self):
        who      = self.ui.textEdit_14
        sentence = EnglishPractice.verb_tense[8]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_15)
    def ui_verbTense10Changed(self):
        who      = self.ui.textEdit_15
        sentence = EnglishPractice.verb_tense[9]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_16)
    def ui_verbTense11Changed(self):
        who      = self.ui.textEdit_16
        sentence = EnglishPractice.verb_tense[10]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_17)
    def ui_verbTense12Changed(self):
        who      = self.ui.textEdit_17
        sentence = EnglishPractice.verb_tense[11]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_18)
    def ui_verbTense13Changed(self):
        who      = self.ui.textEdit_18
        sentence = EnglishPractice.verb_tense[12]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_19)
    def ui_verbTense14Changed(self):
        who      = self.ui.textEdit_19
        sentence = EnglishPractice.verb_tense[13]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_20)
    def ui_verbTense15Changed(self):
        who      = self.ui.textEdit_20
        sentence = EnglishPractice.verb_tense[14]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)
        if '\t' in input_sentence:
            self.ui_focusNextEdit(who,input_sentence.strip(),self.ui.textEdit_21)
    def ui_verbTense16Changed(self):
        who      = self.ui.textEdit_21
        sentence = EnglishPractice.verb_tense[15]
        input_sentence = who.toPlainText()
        self.ui_verbTenseDiff(who, input_sentence, sentence)

    def ui_selectReview(self):
        self.ui.label_113.setVisible(False)
        self.ui.label_114.setVisible(False)
        self.ui.label_115.setVisible(False)
        self.ui.lineEdit_11.setVisible(False)
        self.ui.checkBox.setVisible(False)
        self.ui.checkBox_2.setVisible(False)
        self.ui.checkBox_4.setVisible(False)
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
        self.ui.label_113.setVisible(True)
        self.ui.label_115.setVisible(True)
        self.ui.lineEdit_11.setVisible(True)
        self.ui.checkBox.setVisible(True)
        self.ui.checkBox_2.setVisible(True)
        self.ui.checkBox_4.setVisible(False)
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
        self.ui_wordSourceChanged()
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
            self.wordIndex = 0
            self.p_list    = []
            self.f_generateWords()
        if self.wordMode != 2:
            if self.ui.checkBox_2.isChecked() == False:
                self.ui.checkBox.setChecked(False)
                self.ui.checkBox.setEnabled(False)
                self.ui.checkBox_3.setVisible(False)
            else:
                self.ui.checkBox.setEnabled(True)
                self.ui.checkBox_3.setVisible(True)
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
        self.ui_onGoClicked()

    def ui_similarityChanged(self):
        self.ui_selectNew()

    def fun_getNewWords(self):
        # 获取新词汇
        res = self.fun_initWords()

    def fun_initWords(self):
        def is_between_0_and_1(value):
            try:
                # 尝试将输入转换为浮点数
                num = float(value)
                # 检查数字是否在0到1之间（包括0和1）
                return 0 < num < 1, num
            except ValueError:
                # 如果转换失败（即输入不是数字），返回False
                return False, None
        res = False
        for table in EnglishPractice.vocabulary_list:
            if self.ebdb.tableExist(table) == False:
                self.writeEbbinghaus.createEbbinghausTable(table)
        if self.practiceMode == EnglishPractice.practiceModeList[0]:
            res = True
            # 从数据库中取数据
            valid, similarity = is_between_0_and_1(self.ui.lineEdit_11.text())
            if valid:
                sim_words = []
                all_words = self.db.getAllWords()
                all_words.sort(key=str.lower)
                word_index = 0
                while word_index < len(all_words) - 1:
                    in1 = all_words[word_index]
                    in2 = all_words[word_index+1]
                    sim = self.fun_wordSimilarity(in1, in2)
                    if sim > similarity and sim < 1:
                        if in1 not in sim_words:
                            sim_words.append(in1)
                        if in2 not in sim_words:
                            sim_words.append(in2)
                    word_index += 1
                self.words = sim_words
                len_sim = len(self.words)
                self.wordsNum = min(self.wordsNum,len_sim)
                if len_sim > 0 and valid:
                    self.ui.label_114.setVisible(True)
                    string = "%d words meeting the similarity criteria."%(len_sim)
                    self.ui.label_114.setText(string)
                else:
                    self.ui.label_114.setVisible(False)
                    self.ui.label_114.setText("")                
            else:
                self.wordsNum = int(self.ui.lineEdit.text())
                self.ui.label_114.setVisible(False)
                self.words = self.db.get_randomly(self.wordsNum)
            # 进度条初始化
            self.ui.progressBar.setMinimum(1)
            self.ui.progressBar.setMaximum(self.wordsNum)
            if self.generateAllWords:
                self.words = self.db.getAllWords()
            # 生成单词文件
            self.db_getWords()
            self.f_generateWords()
        elif self.practiceMode == EnglishPractice.practiceModeList[1]:
            res = self.f_getWords()
        elif self.practiceMode == EnglishPractice.practiceModeList[2]:
            self.ebWords     = self.ebdb.getWords(self.EbbinghausTable,self.useSentenceScore)
            res              = self.eb_getEbbinghausWords()
        if len(self.words) > 0:
            self.currentWord = self.words[self.wordIndex]
            if self.practiceMode == EnglishPractice.practiceModeList[1]:
                self.ui_ttsVisible()
        return res

    def fun_markedOnly(self):
        self.ui_renewUI()

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
                if self.ui.checkBox_4.isChecked() == False:
                    selectedWords.append(word)
                    cnt += 1
                    if cnt >= self.wordsNum:
                        break
                else:
                    if self.ebdb.getMarked(word) is not None:
                        if int(self.ebdb.getMarked(word)) == 1:
                            selectedWords.append(word)
                            cnt += 1
                            if cnt >= self.wordsNum:
                                break
                        else:
                            continue
        selectedList = selectedWords[:min(cnt,self.wordsNum)]

        if self.ui.checkBox_4.isChecked() == False:
            if len(selectedList) > 0:
                self.words = selectedList
            else:
                wordsCnt = min(self.wordsNum,len(self.ebWords) if len(self.ebWords)>0 else self.wordsNum)
                self.words = self.db.get_randomly(wordsCnt,self.ebWords)
        else:
            self.words = selectedList

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
        self.EbbinghausTable = self.ui.comboBox.currentText()
        self.ebWords         = self.ebdb.getWords(self.EbbinghausTable,self.useSentenceScore)
        self.db.getWords(self.EbbinghausTable)          
        self.ui_renewUI()
        self.db_getWords()

    def ui_sentenceSourceChanged(self):
        self.listeningTable = self.ui.comboBox_2.currentText()
        self.listenCount    = self.db.getListenContent(self.listeningTable)
        self.ui.label_10.setText(str(self.listenCount))
        self.ui.lineEdit_2.setText("1")
        self.ui.lineEdit_3.setText(str(self.listenCount))
        self.ui_listenTTSVisible()

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

    def fun_play_wav(self,wav_path):
        def run_fun_play_wav():
            # 打开WAV音频文件
            wf = wave.open(wav_path, 'rb')

            # 创建PyAudio对象
            p = pyaudio.PyAudio()

            # 打开一个流
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)

            # 读取数据
            data = wf.readframes(1024)

            # 播放
            while data:
                stream.write(data)
                data = wf.readframes(1024)

            # 停止流
            stream.stop_stream()
            stream.close()

            # 关闭PyAudio
            p.terminate()
        # Create and start the thread
        wav_thread = threading.Thread(target=run_fun_play_wav)
        wav_thread.start()
    def ui_wordUKClicked(self):
        wav_file = "wav/"+self.EbbinghausTable+"/words_uk/"+self.currentWord+".wav"
        self.fun_play_wav(wav_file)
    def ui_wordUSClicked(self):
        wav_file = "wav/"+self.EbbinghausTable+"/words_us/"+self.currentWord+".wav"
        self.fun_play_wav(wav_file)
    def ui_sentenceUSClicked(self):
        import re
        def sanitize_filename(filename):
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        sentence_file = sanitize_filename(self.sentences.get(self.currentWord) if self.sentences.get(self.currentWord) is not None else "All done.")
        wav_file = "wav/"+self.EbbinghausTable+"/sentences_us/"+sentence_file+".wav"
        self.fun_play_wav(wav_file)
    def ui_sentenceUKClicked(self):
        import re
        def sanitize_filename(filename):
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        sentence_file = sanitize_filename(self.sentences.get(self.currentWord) if self.sentences.get(self.currentWord) is not None else "All done.")
        wav_file = "wav/"+self.EbbinghausTable+"/sentences_uk/"+sentence_file+".wav"
        self.fun_play_wav(wav_file)
    def ui_translationClicked(self):
        import re
        def sanitize_filename(filename):
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        translation_file = sanitize_filename(self.translations.get(self.currentWord) if self.translations.get(self.currentWord) is not None else "All done.")
        wav_file = "wav/"+self.EbbinghausTable+"/translations/"+translation_file+".wav"
        self.fun_play_wav(wav_file)
    def f_check_file(self,file_path):
        if os.path.exists(file_path):
            return True
        else:
            return False
    def ui_ttsVisible(self):
        import re
        def sanitize_filename(filename):
            sanitized = re.sub(r'[\<\>:"/|?*]', '_', filename)
            return sanitized
        self.ui.pushButton_21.setVisible(False)
        self.ui.pushButton_22.setVisible(False)
        self.ui.pushButton_23.setVisible(False)
        self.ui.pushButton_24.setVisible(False)
        self.ui.pushButton_25.setVisible(False)
        if self.f_check_file("wav/"+self.EbbinghausTable+"/words_us/"+self.currentWord+".wav"):
            self.ui.pushButton_22.setVisible(True)
        if self.f_check_file("wav/"+self.EbbinghausTable+"/words_uk/"+self.currentWord+".wav"):
            self.ui.pushButton_21.setVisible(True)
        sentence_file = sanitize_filename(self.sentences.get(self.currentWord) if self.sentences.get(self.currentWord) is not None else "All done.")
        if self.f_check_file("wav/"+self.EbbinghausTable+"/sentences_us/"+sentence_file+".wav"):
            self.ui.pushButton_24.setVisible(True)
        if self.f_check_file("wav/"+self.EbbinghausTable+"/sentences_uk/"+sentence_file+".wav"):
            self.ui.pushButton_25.setVisible(True)
        translation_file = sanitize_filename(self.translations.get(self.currentWord) if self.translations.get(self.currentWord) is not None else "All done.")
        if self.f_check_file("wav/"+self.EbbinghausTable+"/translations/"+translation_file+".wav"):
            self.ui.pushButton_23.setVisible(True) 
    def ui_update_text(self, text):
        """这个方法在主线程中被调用来更新UI"""
        string = self.ui.textBrowser_3.toPlainText()
        text = string + text
        self.ui.textBrowser_3.setText(text)
    def fun_online_translate(self, text):
        cn_mean = self.fun_safe_translate(self.translator,text)
        if cn_mean is not None:
            self.update_text_signal.emit('中文直译：'+cn_mean+'\n\n')
    def fun_online_dictionary(self,word):
        en_mean = ""
        res= self.dictionary.meaning(word)
        if res is not None:
            for i in res:
                cnt = 0
                en_mean += i + ":\n"
                for j in res[i]:
                    cnt += 1
                    en_mean += str(cnt) + '. ' + j + '; ' + '\n'
                en_mean += '\n'
            self.update_text_signal.emit(en_mean)
    def ui_onTextEditChanged(self):
        '''
        输入单词发生变化时的回调函数。
        '''
        self.input_word = self.ui.textEdit.toPlainText()
        if self.lastCurrent != self.currentWord:
            self.lastCurrent = self.currentWord
            self.lastInput   = ""
            self.typeCnt     = 0
            self.ui.checkBox_3.setChecked(False)
            self.ui_ttsVisible()
            cn_str = self.meanings.get(self.currentWord)
            cn_str = self.db.mean_cn(self.currentWord,EnglishPractice.SINGLE_MEAN,cn_str)
            if self.ttsMode == 'en':
                self.speak(self.currentWord, cn_str)
            elif self.ttsMode == 'cn':
                self.speak_cn(cn_str)
            if self.netOK:
                self.ui.textBrowser_3.clear()
                en_dict = threading.Thread(target=self.fun_online_dictionary,args=(self.currentWord,))
                en_dict.start()
                cn_dict = threading.Thread(target=self.fun_online_translate,args=(self.currentWord,))
                cn_dict.start()
        else:
            if self.lastInput.strip() != self.input_word.strip():
                if len(self.lastInput.strip()) == 0:
                    self.typeCnt = len(self.input_word.strip())
                self.lastInput = self.input_word.strip()
                if not len(self.input_word.strip()) == len(self.currentWord) or not len(self.lastInput.strip()) == 0:
                    self.typeCnt += 1
        if self.wordModeLast != self.wordMode:
            self.wordModeLast = self.wordMode
            self.ignore_once = True
        else:
            self.ignore_once = False
        self.ui_setWordFont() 
        if len(self.input_word) == 0 and self.ignore_once:
            self.typeCnt = 0
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
            self.ignoreTTS = False
            self.tts_SpeedChange()
            self.tts_AccentChange()
            if self.wordMode == 2 or (self.wordMode == 1 and self.ui.checkBox_2.isChecked()) or (self.wordMode == 0 and self.ui.checkBox_2.isChecked()):
                if self.typeCnt > len(self.currentWord) + 1 or (self.useSentenceScore and self.ui.checkBox_3.isChecked()):
                    self.ui.checkBox_3.setChecked(True)
                else:
                    self.ui.checkBox_3.setChecked(False)
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
            self.speak(self.sentences.get(self.currentWord) if self.sentences.get(self.currentWord) is not None else "All done.")
        if '\t' in self.input_word:
            self.ui_onNextClicked()
            self.fun_updateMarked()

    def ui_onTextEdit_2Changed(self):
        '''
        输入句子发生变化时的回调函数。
        '''
        self.input_sentence = self.ui.textEdit_2.toPlainText()
        self.fun_diffSentence(self.input_sentence,self.sentences.get(self.currentWord) if self.sentences.get(self.currentWord) is not None else "All done.")
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
    
    def fun_wordSimilarity(self, in1, in2):
        import difflib
        similarity = difflib.SequenceMatcher(None, in1.strip(), in2.strip()).quick_ratio()
        return similarity

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
        words_report = self.ebdb.getWords(self.EbbinghausTable,self.useSentenceScore)
        from datetime import datetime
        with open("reports/"+str(datetime.now()).replace(':','-')+".html","w",encoding='utf-8') as file:
            file.write('<table>\n')
            file.write('''    <tr align="left">
        <th bgcolor="#F6F6F6"> LineNo.</th>
        <th bgcolor="#F6F6F6"> Word</th>
        <th bgcolor="#F6F6F6"> <font color="#FE642E"> Score</th>
        <th bgcolor="#F6F6F6"> <font color="#04B431"> Word Count</th>
        <th bgcolor="#F6F6F6"> <font color="#045FB4"> Sentence Count</th>
        <th bgcolor="#F6F6F6"> Marked</th>
    </tr>''')
            index = 0
            lineNo = 0
            for word in words_report:
                lineNo += 1
                if index % 2 == 0:
                    file.write('''
    <tr >
        <td bgcolor="#FDFDFD"> %d</td>
        <td bgcolor="#FDFDFD"> %s</td>
        <td bgcolor="#FDFDFD"> <font color="#FE642E">%s</td>
        <td bgcolor="#FDFDFD"> <font color="#04B431">%s</td>
        <td bgcolor="#FDFDFD"> <font color="#045FB4">%s</td>
        <td bgcolor="#FDFDFD"> %s</td>
    </tr>'''%(lineNo,word,str(self.ebdb.score(word)),str(self.ebdb.wordCount(word)), str(self.ebdb.sentenceCount(word)), str(self.ebdb.getMarked(word))))
                else:
                    file.write('''
    <tr >
        <td bgcolor="#FDFDFD"> %d</td>
        <td bgcolor="#F6F6F6"> %s</td>
        <td bgcolor="#F6F6F6"> <font color="#FE642E">%s</td>
        <td bgcolor="#F6F6F6"> <font color="#04B431">%s</td>
        <td bgcolor="#F6F6F6"> <font color="#045FB4">%s</td>
        <td bgcolor="#F6F6F6"> %s</td>
    </tr>'''%(lineNo, word,str(self.ebdb.score(word)),str(self.ebdb.wordCount(word)), str(self.ebdb.sentenceCount(word)), str(self.ebdb.getMarked(word))))
                index += 1
            file.write('\n</table>\n')
        self.ebdb.close()

    def ui_vedioPausePaly(self):
        self.ytb.sendSpace()

    def ui_skipAd(self):
        self.ytb.skipAd()

    def ui_openYoutube(self):
        if WAV.VALID:
            self.autoTimer.stop()
            self.autoTimerState = False
        self.ui.pushButton_31.setVisible(False)
        self.ytb.open_youtube(self.ui.lineEdit_5.text().strip())

    def ui_againClicked(self):
        self.ytb.again()

    def ui_back5sClicked(self):
        self.ytb.back5s()

    def ui_onceMoreClicked(self):
        self.wordIndex = 0
        self.p_list    = []
        self.f_generateWords()
        self.ui_renewUI()

    def ui_setWordFromIndex(self, index):
        if len(self.words) == 0:
            self.words.append("All done")
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
        if self.practiceMode != EnglishPractice.practiceModeList[1]:
            for word in self.words:
                self.pronunciations[word] = self.db.pronun(word)
                self.meanings      [word] = self.db.mean(word,EnglishPractice.SINGLE_MEAN)
                self.sentences     [word] = self.db.sentence(word)
                self.translations  [word] = self.db.trans(word)

    def f_getWords(self):
        self.p_list = []
        res = True
        try:
            with open("EnglishFiles/words.txt","r",encoding='utf-8') as file:
                word       = None
                self.words = []
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
                        if EnglishPractice.SINGLE_MEAN:
                            content = self.db.split_by_space(word, content)
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
        self.ebWords     = self.ebdb.getWords(self.EbbinghausTable,self.useSentenceScore)
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
                self.writeEbbinghaus.openAndInsert(self.EbbinghausTable,
                                                   input_word,
                                                   self.score,
                                                   word_cnt,
                                                   sentence_cnt,
                                                   datetime.now(),
                                                   sentenceTimestamp,
                                                   int(self.ui.checkBox_3.isChecked()))
            elif self.score > self.sentenceCriteria:
                self.writeEbbinghaus.openAndInsert(self.EbbinghausTable,
                                                   input_word,
                                                   self.score,
                                                   word_cnt,
                                                   sentence_cnt,
                                                   datetime.now(),
                                                   datetime.now(),
                                                   int(self.ui.checkBox_3.isChecked()))
    def f_wordsToFile(self):
        self.words_p_lines = ''
        with open("EnglishFiles/words_p.txt","w",encoding='utf-8') as file:
            for i in self.p_list:
                self.words_p_lines += i
            file.write(self.words_p_lines.rstrip())
    def f_generateWords(self):
        self.words_p_lines = ''
        if len(self.words) == 0 or self.words[0] == "All done":
            return
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
        self.p_list        = []
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