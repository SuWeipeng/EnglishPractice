import sqlite3

class WriteEbbinghausDB:
    def __init__(self,db_name):
        self.db_name   = "database/" + db_name
        self.open()
    def open(self):
        # 创建数据库连接
        self.mem_conn  = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES |
                                                                  sqlite3.PARSE_COLNAMES)
        self.disk_conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES |
                                                                    sqlite3.PARSE_COLNAMES)
        # 将本地数据库备份到内存数据库
        self.disk_conn.backup(self.mem_conn)
    def createEbbinghausTable(self,table):
        self.open()
        sql = "CREATE TABLE IF NOT EXISTS %s(id INTEGER PRIMARY KEY, word VARCHAR, score DOUBLE, word_base INTEGER, sentence_base INTEGER, word_time TIMESTAMP, sentence_time TIMESTAMP, marked INTEGER)"%(table)
        cursor = self.mem_conn.cursor()
        cursor.execute(sql)
        self.mem_conn.commit()
        self.to_disk()
    def openAndInsert(self, table, word, score, word_base, sentence_base, word_time, sentence_time, marked):
        self.open()
        cursor = self.mem_conn.cursor()
        # 检查 word 是否已存在并获取其 id
        cursor.execute(f"SELECT id FROM {table} WHERE word = ?", (word,))
        result = cursor.fetchone()
        if result:
            id = result[0]  # 使用现有的 id
        else:
            # 获取当前最大的 id 值
            cursor.execute(f"SELECT MAX(id) FROM {table}")
            max_id = cursor.fetchone()[0]
            id = 1 if max_id is None else max_id + 1  # 如果表为空，从 1 开始，否则使用 max_id + 1
        # 插入或更新行
        sql = "INSERT OR REPLACE INTO %s VALUES(?,?,?,?,?,?,?,?)"%(table)
        cursor.execute(sql, (id, word, score, word_base, sentence_base, word_time, sentence_time, marked))
        self.mem_conn.commit()
        self.to_disk()
    def to_disk(self):
        self.mem_conn.backup(self.disk_conn)
        self.mem_conn.close()
        self.disk_conn.close()

def main():
    db = WriteEbbinghausDB("Ebbinghaus.db")
    from datetime import datetime
    db.createEbbinghausTable("test_code")
    db.openAndInsert("test_code","a",1,1,1,datetime.now(),datetime.now(),0)
    
if __name__ == '__main__':
    main()