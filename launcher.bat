@echo off
cd G:\Projeto API Spark\
call C:\Python\python.exe TGSPAR.py >> LOG_TGSPAR.txt 2>&1
call C:\Python\python.exe TGSCAB.py >> LOG_TGSCAB.txt 2>&1
call C:\Python\python.exe TGSITE.py >> LOG_TGSITE.txt 2>&1
call C:\Python\python.exe TGSSER.py >> LOG_TGSSER.txt 2>&1
