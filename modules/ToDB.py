import sqlite3

class ToDB:
    def __init__(self,db_name):
        self.db_name   = "database/" + db_name
        self.tableName = None
        # 创建数据库连接
        self.mem_conn  = sqlite3.connect(":memory:")
        self.disk_conn = sqlite3.connect(self.db_name)
        # 将本地数据库备份到内存数据库
        self.disk_conn.backup(self.mem_conn)
    def createTable(self,tableName):
        self.tableName = tableName
        # 在 mem_conn 创建 vacabulary 表
        self.createVacabularyTable(self.mem_conn)
    def createVacabularyTable(self,conn):
        sql = "CREATE TABLE IF NOT EXISTS %s (word VARCHAR PRIMARY KEY, pronun VARCHAR, mean VARCHAR, example VARCHAR, trans VARCHAR)"%(self.tableName)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
    def insertVocabulary(self,word,pronun,mean,example,trans,replace = False):
        cmd = "INTO %s VALUES(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')"%(self.tableName,word,pronun,mean,example,trans)
        if replace:
            sql = "INSERT OR REPLACE " + cmd
        else:
            sql = "INSERT OR IGNORE " + cmd
        cursor = self.mem_conn.cursor()
        cursor.execute(sql)
        self.mem_conn.commit()

    def to_disk(self):
        self.mem_conn.backup(self.disk_conn)
        self.mem_conn.close()
        self.disk_conn.close()

def main():
    db = ToDB("English.db")
    #db.to_disk()
    
if __name__ == '__main__':
    main()