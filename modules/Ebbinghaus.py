class Ebbinghaus:
    def __init__(self):
        self.wordsFiltered = []
        self.criteria = {1:12,
                         2:24,
                         3:48,
                         4:96,
                         5:192,
                         6:384}
    def setWords(self,words):
        self.allWords = words
    def check(self,count,timestamp,score=0):
        import datetime
        res = False
        criteria = None
        # 确定判定标准
        if count in self.criteria:
            criteria = self.criteria.get(count)
        elif count >= 6:
            criteria = self.criteria.get(6)
        if score > 0:
            criteria = int(criteria * score)
        # 按标准计算下一次的时间
        next_timestamp = timestamp+datetime.timedelta(hours=criteria)
        # 若当前已到达判定时间，则将返回值置为 True
        if next_timestamp < datetime.datetime.now():
            res = True
        return res

def main():
    import datetime
    eb = Ebbinghaus()
    res = eb.check(17,datetime.datetime.now())
    print(res)
    
if __name__ == '__main__':
    main()