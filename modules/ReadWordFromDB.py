import sqlite3

class ReadWordFromDB:
    def __init__(self,db_name,tableName,listenTable):
        self.db_name     = "database/" + db_name
        self.tableName   = tableName
        self.listenTable = listenTable
        # 创建数据库连接
        self.mem_conn  = sqlite3.connect(":memory:")
        self.disk_conn = sqlite3.connect(self.db_name)
        # 将本地数据库备份到内存数据库
        self.disk_conn.backup(self.mem_conn)
        self.getWords()
    def getTables(self):
        '''
        获取数据库里所有表的名字。
        '''
        tables = []
        SQLITE_CMD = 'SELECT * FROM sqlite_master WHERE type=\'table\''
        with self.mem_conn:
            cur = self.mem_conn.cursor()
            cur.execute(SQLITE_CMD)
            rows = cur.fetchall()
        for row in rows:
            tables.append(row[1])
        return tables
    def getListenContent(self,table=None):
        self.links               = []
        self.listenSentences     = []
        self.listenTranslations  = []
        self.listenCount         = 0
        targetTable = self.listenTable
        if table is not None:
            self.listenTable = table
            targetTable = self.listenTable
        SQLITE_CMD = 'SELECT * FROM %s'%(targetTable)
        with self.mem_conn:
            cur = self.mem_conn.cursor()
            cur.execute(SQLITE_CMD)
            rows = cur.fetchall()
        for row in rows:
            self.links.append(row[2])
            self.listenSentences.append(row[1])
            self.listenTranslations.append(row[3])
        self.listenCount = len(self.links)
        return self.listenCount
    
    def getListenLink(self,index):
        return self.links[index]

    def getListenSentence(self,index):
        return self.listenSentences[index]
    
    def getListenTranslation(self,index):
        return self.listenTranslations[index]

    def getWords(self,table=None):
        '''
        从数据库的 vocabulary 表获取全部单词数据
        '''
        self.words            = []
        self.pronunciations   = {}
        self.meanings         = {}
        self.sentences        = {}
        self.translations     = {}
        targetTable = self.tableName
        if table is not None:
            self.tableName = table
            targetTable    = self.tableName
        SQLITE_CMD = 'SELECT * FROM %s'%(targetTable)
        with self.mem_conn:
            cur = self.mem_conn.cursor()
            cur.execute(SQLITE_CMD)
            rows = cur.fetchall()
        for row in rows:
            self.words.append(row[0])
            self.pronunciations [row[0]] = row[1]
            self.meanings       [row[0]] = row[2]
            self.sentences      [row[0]] = row[3]
            self.translations   [row[0]] = row[4]
    def word_exist(self,word):
        res = None
        if word in self.words:
            res = True
        return res
    def pronun(self,word):
        return self.pronunciations.get(word)
    def mean(self,word):
        return self.meanings.get(word)
    def sentence(self,word):
        return self.sentences.get(word)
    def trans(self,word):
        return self.translations.get(word)
    def get_randomly(self,N,expel=None):
        import random
        res = random.sample(self.words,N)
        if expel is not None:
            s1 = set(self.words)
            s2 = set(expel)
            sr = s1 - s2
            res = list(sr)
            res = random.sample(res,N)
        return res
    def getAllWords(self):
        return self.words

def main():
    db = ReadWordFromDB("English.db","IELTS1000")
    print(db.get_randomly(10))
    
if __name__ == '__main__':
    main()