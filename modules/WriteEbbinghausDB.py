import sqlite3

class WriteEbbinghausDB:
    def __init__(self,db_name):
        self.db_name   = "database/" + db_name
        # 创建数据库连接
        self.mem_conn  = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES |
                                                                  sqlite3.PARSE_COLNAMES)
        self.disk_conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES |
                                                                    sqlite3.PARSE_COLNAMES)
        # 将本地数据库备份到内存数据库
        self.disk_conn.backup(self.mem_conn)
        # 在 mem_conn 创建 vacabulary 表
        self.createVacabularyTable(self.mem_conn)
        self.to_disk()
    def createVacabularyTable(self,conn):
        sql = "CREATE TABLE IF NOT EXISTS vacabulary(word VARCHAR PRIMARY KEY, score DOUBLE, word_base INTEGER, sentence_base INTEGER, word_time TIMESTAMP, sentence_time TIMESTAMP)"
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
    def openAndInsert(self,word,score,word_base,sentence_base,word_time,sentence_time):
        # 创建数据库连接
        self.mem_conn  = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES |
                                                                  sqlite3.PARSE_COLNAMES)
        self.disk_conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES |
                                                                    sqlite3.PARSE_COLNAMES)
        # 将本地数据库备份到内存数据库
        self.disk_conn.backup(self.mem_conn)
        sql = "INSERT OR REPLACE INTO vacabulary VALUES(?,?,?,?,?,?)"
        cursor = self.mem_conn.cursor()
        cursor.execute(sql, (word,score,word_base,sentence_base,word_time,sentence_time))
        self.mem_conn.commit()

        self.mem_conn.backup(self.disk_conn)
        self.mem_conn.close()
        self.disk_conn.close()
    def to_disk(self):
        self.mem_conn.backup(self.disk_conn)
        self.mem_conn.close()
        self.disk_conn.close()

def main():
    db = WriteEbbinghausDB("Ebbinghaus.db")
    from datetime import datetime
    db.openAndInsert("a",1,1,1,datetime.now(),datetime.now())
    
if __name__ == '__main__':
    main()