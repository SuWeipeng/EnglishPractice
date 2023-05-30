import os

'''
L_10 带例句，源于《单字库》 APP 的 IELTS 词汇
'''
fileName       = "L_10"

'''
mode 的取值如下：
1:生成默写文件
2:摘错词
3:生成带例句的默写文件
'''
mode           = 3

targetFile     = fileName+".txt"
targetFullPath = None
outputFileName = targetFile.split(".")[0]+"_P.prc"

def generate_prc():
    output         = open(outputFileName,"w",encoding='utf-8')
    for dirName, subdirList, fileList in os.walk(os.getcwd()):
        for fname in fileList:
            if fname == targetFile:
                targetFullPath = ('%s' % dirName+'\\'+fname)
    with open(targetFullPath,"r",encoding='utf-8') as file:
        for i, line in enumerate(file):
            if i % 2 != 0:
                output.write("\n")
                output.write(line)
                
    output.close()

import re
errorFile       = fileName+"_Err.txt"
outputFileName2 = targetFile.split(".")[0]+"_E.prc"
def generate_from_err():
    output         = open(outputFileName2,"w",encoding='utf-8')
    for dirName, subdirList, fileList in os.walk(os.getcwd()):
        for fname in fileList:
            if fname == errorFile:
                targetFullPath = ('%s' % dirName+'\\'+fname)
    with open(targetFullPath,"r",encoding='utf-8') as file:
        for i, line in enumerate(file):
            new_line = re.sub(r"\(.*?\)", "()", line)
            output.write(new_line)
            
    output.close()       

def generate_prc2():
    output         = open(outputFileName,"w",encoding='utf-8')
    for dirName, subdirList, fileList in os.walk(os.getcwd()):
        for fname in fileList:
            if fname == targetFile:
                targetFullPath = ('%s' % dirName+'\\'+fname)
    with open(targetFullPath,"r",encoding='utf-8') as file:
        IGNORE_LINES = 0
        for i, line in enumerate(file):
            if IGNORE_LINES > 0:
                IGNORE_LINES -= 1
                continue
            if i % 4 == 0: # 单词行
                # 在记住的单词行前加 @ 会在生成的文件中去除该词（用于消除记住的词）
                if line[0] == '@':
                    IGNORE_LINES = 3
                    continue
                else:
                    output.write("\n")
            elif i % 4 == 2: # 列句行
                new_line = re.sub(r"\(.*?\)", "()", line)
                output.write(new_line)
            else:
                output.write(line)

    output.close()

def main():
    if mode == 1:
        generate_prc()
    elif mode == 3:
        generate_prc2()
    else:
        generate_from_err()
    
if __name__ == '__main__':
    main()