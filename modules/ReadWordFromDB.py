import sqlite3

class ReadWordFromDB:
    def __init__(self,db_name):
        self.words            = []
        self.pronunciations   = {}
        self.meanings         = {}
        self.sentences        = {}
        self.translations     = {}
        self.db_name   = "database/" + db_name
        # 创建数据库连接
        self.mem_conn  = sqlite3.connect(":memory:")
        self.disk_conn = sqlite3.connect(self.db_name)
        # 将本地数据库备份到内存数据库
        self.disk_conn.backup(self.mem_conn)
        self.getWords()
    def getWords(self):
        '''
        从数据库的 vocabulary 表获取全部单词数据
        '''
        SQLITE_CMD = 'SELECT * FROM vacabulary'
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
    def get_randomly(self,N):
        import random
        return random.sample(self.words,N)

def main():
    db = ReadWordFromDB("English.db")
    print(db.get_randomly(10))
    
if __name__ == '__main__':
    main()