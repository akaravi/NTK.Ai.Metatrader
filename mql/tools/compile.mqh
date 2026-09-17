//+------------------------------------------------------------------+
//|                                                      compile.mq5 |
//|                                      Copyright 2026,JBlanked LLC |
//|                                         https://www.jblanked.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked LLC"
#property link      "https://www.jblanked.com"
#property version   "1.00"
#property strict

#import "shell32.dll"
int ShellExecuteW(int hWnd, string lpOperation, string lpFile, string lpParameters, string lpDirectory, int nShowCmd);
#import

#ifndef COMMON_FOLDER
#define COMMON_FOLDER TerminalInfoString(TERMINAL_COMMONDATA_PATH) + "\\" + "Files" + "\\"
#endif

#ifndef META_EDITOR
#define META_EDITOR TerminalInfoString(TERMINAL_PATH) + "\\metaeditor64.exe"
#endif

//+------------------------------------------------------------------+
//| Compile an .mq5 expert advisor; provide path, returns log output |
//+------------------------------------------------------------------+
string compileMql5(string mq5_path, uint timeoutMs = 60000)
{
   const int fileExtensionPosition = StringFind(mq5_path, ".mq5");
   if(fileExtensionPosition < 0) return "[Build Error]: Invalid file type. Expected `.mq5`";

   if(!FolderCreate(".compile", FILE_COMMON)) return "[Build Error]: Failed to create log folder";

   int slash = -1;
   for(int i = fileExtensionPosition; i >= 0; i--)
   {
      if(mq5_path[i] == 92)
      {
         slash = i;
         break;
      }
   }

   const string mq5FileName = StringSubstr(mq5_path, slash + 1);
   const string mq5RootPath = StringSubstr(mq5_path, 0, slash + 1);
   const string fileName = StringSubstr(mq5FileName, 0, StringFind(mq5FileName, ".mq5"));
   const string fileLogName = fileName + ".log";
   const string doneFileName = fileName + ".done";

   const string loggerPath = mq5RootPath + fileLogName;
   const string commonLogRel = ".compile\\" + fileLogName;
   const string commonLogPath = COMMON_FOLDER + commonLogRel;
   const string commonDoneRel = ".compile\\" + doneFileName;
   const string commonDonePath = COMMON_FOLDER + commonDoneRel;

   if(::FileIsExist(commonLogRel, FILE_COMMON))  ::FileDelete(commonLogRel, FILE_COMMON);
   if(::FileIsExist(commonDoneRel, FILE_COMMON)) ::FileDelete(commonDoneRel, FILE_COMMON);

   const string innerCmd = StringFormat("\"%s\" /compile:\"%s\" /log & copy /Y \"%s\" \"%s\" & echo done> \"%s\"", META_EDITOR, mq5_path, loggerPath, commonLogPath, commonDonePath);
   const string shellParams = StringFormat("/C \"%s\"", innerCmd);

   const int result = ShellExecuteW(0, "open", "cmd.exe", shellParams, "", 0);
   if(result < 32) return StringFormat("[Build Error]: ShellExecute failed, code (%d)", result);

   const uint start = GetTickCount();
   bool done = false;
   while(GetTickCount() - start < timeoutMs)
   {
      if(::FileIsExist(commonDoneRel, FILE_COMMON))
      {
         done = true;
         break;
      }
      Sleep(100);
   }

   if(!done) return StringFormat("[Build Error]: Timed out waiting for compile to finish (%d ms): %s", timeoutMs, loggerPath);

   if(!::FileIsExist(commonLogRel, FILE_COMMON))
      return StringFormat("[Build Error]: Log file not found after compile: %s", commonLogPath);

   int handle = ::FileOpen(commonLogRel, FILE_READ | FILE_COMMON | FILE_TXT | FILE_ANSI);
   if (handle == INVALID_HANDLE) return StringFormat("[Build Error]: Error '%d', could not open file: %s", GetLastError(), commonLogPath);

   string content = "";
   while (!::FileIsEnding(handle))
      content += ::FileReadString(handle) + "\n";
   ::FileClose(handle);

   ::FileDelete(commonDoneRel, FILE_COMMON);

   return StringLen(content) > 0 ? content : "[Build Error]: Log file is empty";
}
//+------------------------------------------------------------------+
