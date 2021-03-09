import os
   
targetFile     = "L_01.txt"
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
errorFile      = "L_01_Err.txt"
outputFileName = targetFile.split(".")[0]+"_E.prc"
def generate_from_err():
    output         = open(outputFileName,"w",encoding='utf-8')
    for dirName, subdirList, fileList in os.walk(os.getcwd()):
        for fname in fileList:
            if fname == errorFile:
                targetFullPath = ('%s' % dirName+'\\'+fname)
    with open(targetFullPath,"r",encoding='utf-8') as file:
        for i, line in enumerate(file):
            new_line = re.sub(r"\(.*?\)", "()", line)
            output.write(new_line)
            
    output.close()       

def main():
    generate_from_err()
    
if __name__ == '__main__':
    main()