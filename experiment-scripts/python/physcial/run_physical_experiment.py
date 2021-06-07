#!/usr/bin/env python3
import subprocess
import csv
import json

import sys
import os

import time 

def writeCsv(file, row):

    with open(file, 'a') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(row)

        
def run_df(dir):

    result = subprocess.check_output(['du', '-s', '-B', '1', dir], encoding='utf-8')
    result = result.split('\t')[0]
#    result = (((result.split('\t'))[0]).split(' '))[0]
    result = float(result)
    return result

def dedupZfs():

    result = subprocess.check_output(['zpool', 'list'], encoding='utf-8')
    result = (result.split('\n')[1]).split(' ')

    res = ''
    for elm in result:
        # Only the ratio ends with x
        if elm.endswith('x'):
            res = elm[:-1]
            break
    return res
    

def copy(input, output):

    start = time.time()
    subprocess.call(['cp', input, output], encoding="utf-8")
    end = time.time()
    result = end - start
    return result

def main(configFilePath):

    config = None
    with open(configFilePath, 'r') as configFile:
        data = configFile.read()
        config = json.loads(data)


    fileList = config["file_list"]
    outputDir = config["output_dir"]
    dfDir = outputDir
    
    if 'minerva_dir' in config:
        dfDir = config['minerva_dir']

    interval = config['interval']
    resultFile = config['result_file']

    dedupRatio = None

    if ('dedup_ratio' in config):
        dedupRatio = config["dedup_ratio"]

    
    files = []
    with open(fileList) as fileList:
        files = fileList.readlines()


    print('Starting experiment with config: {!s}'.format(configFilePath))
    print('Writing result to: {!s}'.format(resultFile))
    print('Running with file list: {!s}'.format(fileList))
    print('Total number of files: {!s}'.format(len(files)))
    print('Copiying files to: {!s}'.format(outputDir))
    print('Recording storage usage every {!s} file'.format(interval))
    if dedupRatio:
        print("Recording dedup ratio using style: {!s}".format(dedupRatio))

    
    
    header = []

    if dedupRatio:
        header = ['file', 'original', 'physical end', 'dedup ratio', 'time']
    else:
        header = ['file', 'original', 'physical end', 'time']


    writeCsv(resultFile, header)

    originSize = 0;
    i = 1

    for file in files:

        if file.endswith('\n'):
            file = file[:-1]
        print('File {!s}/{!s}: '.format(i, len(files), file))
        
        file = file
        originSize += os.path.getsize(file)
        delta = copy(file, outputDir)

        finalSize = 0
        recordedDedupRatio = 0
        if ((i % interval == 0) or (i == len(files))):
            finalSize = run_df(dfDir)


            if dedupRatio:
                if dedupRatio == 'zfs':
                    recordedDedupRatio = dedupZfs()
                    # TODO: ZFS
                else:
                    recordedDedupRatio = finalSize / float(originSize)
                
        if dedupRatio:
            writeCsv(resultFile, [i, originSize, finalSize, recordedDedupRatio, delta])
        else:
            writeCsv(resultFile, [i, originSize, finalSize, delta])
        i = i + 1            
            
    print('Copied {!s} files'.format(i))
    print('Written result to: {!s}'.format(resultFile))


if __name__ ==  '__main__':

    configFile = sys.argv[1]
    main(configFile)

        
