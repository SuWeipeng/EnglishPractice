import os
   
targetFile     = "L_01.txt"

targetFullPath = None
outputFileName = targetFile.split(".")[0]+"_P.prc"
lineNo         = 1
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
            lineNo += 1
            
output.close()
            
        
