import sqlite3

class ReadEbbinghausDB:
    def __init__(self,db_name):
        self.words        = []
        self.wordCnt      = {}
        self.sentenceCnt  = {}
        self.wordTime     = {}
        self.sentenceTime = {}
        self.db_name   = "database/" + db_name
        # 创建数据库连接
        self.mem_conn  = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES |
                                                                  sqlite3.PARSE_COLNAMES)
        self.disk_conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES |
                                                                    sqlite3.PARSE_COLNAMES)
        # 将本地数据库备份到内存数据库
        self.disk_conn.backup(self.mem_conn)
        self.getWords()
    def getWords(self,order_by_sentence = False):
        self.words = []
        if order_by_sentence == False:
            SQLITE_CMD = 'SELECT * FROM vacabulary ORDER BY word_base ASC'
        else:
            SQLITE_CMD = 'SELECT * FROM vacabulary ORDER BY sentence_base ASC'
        with self.mem_conn:
            cur = self.mem_conn.cursor()
            cur.execute(SQLITE_CMD)
            rows = cur.fetchall()
        for row in rows:
            self.words.append(row[0])
            self.wordCnt     [row[0]] = row[2]
            self.sentenceCnt [row[0]] = row[3]
            self.wordTime    [row[0]] = row[4]
            self.sentenceTime[row[0]] = row[5]
        return self.words
    def wordCount(self,word):
        return self.wordCnt.get(word)
    def sentenceCount(self,word):
        return self.sentenceCnt.get(word)
    def wordTimestamp(self,word):
        return self.wordTime.get(word)
    def sentenceTimestamp(self,word):
        return self.sentenceTime.get(word)

def main():
    db = ReadEbbinghausDB("Ebbinghaus.db")
    db.getWords()
    
if __name__ == '__main__':
    main()