import sqlite3
import random
import re

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
            self.links.append(row[1])
            self.listenSentences.append(row[2])
            self.listenTranslations.append(row[3])
        self.listenCount = len(self.links)
        return self.listenCount
    
    def getListenLink(self,index):
        return self.links[index]

    def getListenSentence(self,index):
        return self.listenSentences[index]
    
    def getListenTranslation(self,index):
        return self.listenTranslations[index]

    def getRepeat(self,table=None):
        self.id               = []
        self.id_word          = {}
        self.id_pronunciation = {}
        self.id_meaning       = {}
        self.id_sentence      = {}
        self.id_translation   = {}
        targetTable = self.tableName
        if table is not None:
            self.tableName = table
            targetTable    = self.tableName
        SQLITE_CMD = 'SELECT * FROM %s GROUP BY word HAVING COUNT(*)>1'%(targetTable)
        with self.mem_conn:
            cur = self.mem_conn.cursor()
            cur.execute(SQLITE_CMD)
            rows = cur.fetchall()
        if len(rows) == 0:
            return self.id
        else:
            for row in rows:
                SQLITE_CMD = 'SELECT * FROM %s WHERE word=\"%s\"'%(targetTable,row[1])
                cur = self.mem_conn.cursor()
                cur.execute(SQLITE_CMD)
                rows = cur.fetchall()
                for row in rows:
                    self.id.append(row[0])
                    self.id_word[row[0]]          = row[1]
                    self.id_pronunciation[row[0]] = row[2]
                    self.id_meaning[row[0]]       = row[3]
                    self.id_sentence[row[0]]      = row[4]
                    self.id_translation[row[0]]   = row[5]
        return self.id
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
            self.words.append(row[1])
            self.pronunciations [row[1]] = row[2]
            self.meanings       [row[1]] = row[3]
            self.sentences      [row[1]] = row[4]
            self.translations   [row[1]] = row[5]
    def word_exist(self,word):
        res = None
        if word in self.words:
            res = True
        return res
    def pronun(self,word):
        return self.pronunciations.get(word)
    def split_by_cn(self,cn):
        res = ''
        # 移除括号及其内部的内容
        t = re.sub(r'（[^）]*）', '', cn)
        # 使用正则表达式按中文逗号和分号分割
        l = re.split(r'[，；]', t)
        num_l = len(l)
        r = random.randint(0, num_l-1)
        res = l[r]
        return res
    def split_by_space(self, word, mean):
        res = ''
        l = mean.replace(';', ' ')
        l = l.split()
        if len(l) % 2 != 0 or len(l) == 0:
            print("There is something wrong of the word '%s''s meaning."%(word))
        else:
            num_l = int(len(l) / 2)
            r = random.randint(0, num_l-1)
            p = r * 2
            cn = l[p+1]
            cn_1 = self.split_by_cn(cn)
            m = l[p] + ' ' + cn_1
            res = m
        return res
    def mean_cn(self,word,single_mode=False,mean=None):
        if mean is not None:
            l = mean.split()
            if len(l) % 2 != 0 or len(l) == 0:
                print("There is something wrong of the word '%s''s meaning."%(word))
            else:
                res = l[1]
                res = self.split_by_cn(res)
        else:
            res = self.mean(word,single_mode)
        return res

    def mean(self,word,single_mode=False):
        res = self.meanings.get(word)
        if res is not None:
            res = res.strip()
            if single_mode:
                res = self.split_by_space(word, res)
        return res
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
            res = random.sample(res,N if N <= len(sr) else len(sr))
        return res
    def id_w(self,id):
        return self.id_word[id]
    def id_p(self,id):
        return self.id_pronunciation[id]
    def id_m(self,id):
        return self.id_meaning[id]
    def id_s(self,id):
        return self.id_sentence[id]
    def id_t(self,id):
        return self.id_translation[id]
    def getAllWords(self):
        return self.words

def main():
    wordTable = 'IELTS1000'
    db = ReadWordFromDB('English.db',wordTable,'Coversation01')
    repeat_id = db.getRepeat()
    if len(repeat_id) > 0:
        write_str = ''
        with open("EnglishFiles/%s_Repeat.txt"%(wordTable),"w",encoding='utf-8') as file:
            for id in repeat_id:
                write_str += (db.id_w(id).strip())
                write_str += ('\n')
                write_str += (db.id_p(id).strip())
                write_str += ('\n')
                write_str += (db.id_m(id).strip())
                write_str += ('\n')
                write_str += (db.id_s(id).strip())
                write_str += ('\n')
                write_str += (db.id_t(id).strip())
                write_str += ('\n')
            file.write(write_str.rstrip())
        write_str = ''
        with open("EnglishFiles/%s_Repeat_p.txt"%(wordTable),"w",encoding='utf-8') as file:
            for id in repeat_id:
                write_str += ('\n')
                write_str += (db.id_p(id).strip())
                write_str += ('\n')
                write_str += (db.id_m(id).strip())
                write_str += ('\n')
                write_str += ('\n')
                write_str += (db.id_t(id).strip())
                write_str += ('\n')
            file.write(write_str.rstrip())
    
if __name__ == '__main__':
    main()