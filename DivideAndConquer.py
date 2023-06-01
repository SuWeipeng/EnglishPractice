import os,re

'''
L_10 带例句，源于《单字库》 APP 的 IELTS 词汇
'''
fileName       = "L_10"

groupInFile    = 50
groupLines     = 4

row_alignment  = True
#row_alignment  = False

boundaryNo     = groupLines * groupInFile - 1

targetFile     = fileName+".txt"
targetFullPath = None
outputFileNo   = 1
outputFileName = targetFile.split(".")[0]+"_"+str(outputFileNo)+"_P.prc"

IGNORE_LINES   = 0
def process_line(i,line):
    if row_alignment:
        ret = "\n"
    else:
        ret = ""
    global IGNORE_LINES
    if i % 4 == 0: # 单词行
        # 在记住的单词行前加 @ 会在生成的文件中去除该词（用于消除记住的词）
        if line[0] == '@':
            IGNORE_LINES = 4
    if IGNORE_LINES > 0:
        IGNORE_LINES -= 1
    elif i % 4 == 2: # 列句行
        new_line = re.sub(r"\(.*?\)", "()", line)
        ret = new_line
    elif i % 4 == 0: # 单词行
        ret = "\n"
    else:
        ret = line

    return ret

def generate_prc():
    global outputFileName,outputFileNo,boundaryNo
    part_number    = 0
    lines          = 0
    output         = open(outputFileName,"w",encoding='utf-8')
    for dirName, subdirList, fileList in os.walk(os.getcwd()):
        for fname in fileList:
            if fname == targetFile:
                targetFullPath = ('%s' % dirName+'\\'+fname)
    with open(targetFullPath,"r",encoding='utf-8') as file:
        lines = len(file.readlines())
    with open(targetFullPath,"r",encoding='utf-8') as file:
        for i, line in enumerate(file):
            if i > boundaryNo:
                output.close()
                outputFileNo += 1
                boundaryNo = groupLines * groupInFile * outputFileNo - 1
                outputFileName = targetFile.split(".")[0]+"_"+str(outputFileNo)+"_P.prc"
                output         = open(outputFileName,"w",encoding='utf-8')
                output.write(process_line(i,line))
            else:
                output.write(process_line(i,line))
        output.close()


def main():
    generate_prc()
    
if __name__ == '__main__':
    main()