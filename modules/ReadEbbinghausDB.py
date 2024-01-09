import sqlite3

class ReadEbbinghausDB:
    def __init__(self,db_name,table):
        self.words        = []
        self.scores       = {}
        self.wordCnt      = {}
        self.sentenceCnt  = {}
        self.wordTime     = {}
        self.sentenceTime = {}
        self.marked       = {}
        self.db_name   = "database/" + db_name
        self.getWords(table)
    def open(self):
        # 创建数据库连接
        self.mem_conn  = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES |
                                                                  sqlite3.PARSE_COLNAMES)
        self.disk_conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES |
                                                                    sqlite3.PARSE_COLNAMES)
        # 将本地数据库备份到内存数据库
        self.disk_conn.backup(self.mem_conn)
    def close(self):
        self.mem_conn.close()
        self.disk_conn.close()

    def tableExist(self,table):
        res = False
        self.open()
        SQLITE_CMD = 'SELECT count(*) FROM sqlite_master WHERE type="table" AND name = \"%s\"'%(table)
        cur = self.mem_conn.cursor()
        cur.execute(SQLITE_CMD)
        rows = cur.fetchall()
        self.close()
        for row in rows:
            if row[0] > 0:
                res = True
        return res

    def getWords(self,table,order_by_sentence = False):
        self.open()
        self.words        = []
        self.scores       = {}
        self.wordCnt      = {}
        self.sentenceCnt  = {}
        self.wordTime     = {}
        self.sentenceTime = {}
        self.marked       = {}
        if order_by_sentence == False:
            SQLITE_CMD = 'SELECT * FROM %s ORDER BY word_base ASC'%(table)
        else:
            SQLITE_CMD = 'SELECT * FROM %s ORDER BY sentence_base ASC'%(table)
        with self.mem_conn:
            cur = self.mem_conn.cursor()
            cur.execute(SQLITE_CMD)
            rows = cur.fetchall()
        self.close()
        for row in rows:
            self.words.append(row[1])
            self.scores      [row[1]] = row[2]
            self.wordCnt     [row[1]] = row[3]
            self.sentenceCnt [row[1]] = row[4]
            self.wordTime    [row[1]] = row[5]
            self.sentenceTime[row[1]] = row[6]
            self.marked      [row[1]] = row[7]
        return self.words
    def score(self,word):
        return self.scores.get(word)
    def wordCount(self,word):
        return self.wordCnt.get(word)
    def sentenceCount(self,word):
        return self.sentenceCnt.get(word)
    def wordTimestamp(self,word):
        return self.wordTime.get(word)
    def sentenceTimestamp(self,word):
        return self.sentenceTime.get(word)
    def getMarked(self,word):
        return self.marked.get(word)

def main():
    db = ReadEbbinghausDB("Ebbinghaus.db")
    db.getWords()
    
if __name__ == '__main__':
    main()