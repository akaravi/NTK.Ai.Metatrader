//+------------------------------------------------------------------+
//|                                                      context.mqh |
//|                                          Copyright 2026,JBlanked |
//|                                        https://www.jblanked.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked"
#property link      "https://www.jblanked.com/"
#property strict

const string CONTEXT_FILES[] =
{
   "context\\mql.md",
   "context\\trade.md",
   "workflows\\response.md",
};

const string BUILDER_FILES[] =
{
   "context\\builder\\chart.md",
   "context\\builder\\expert-advisor.md",
   "context\\builder\\indicator.md",
   "context\\builder\\object.md",
   "context\\builder\\platform.md",
   "context\\builder\\risk-management.md",
   "context\\builder\\script.md",
   "context\\builder\\strategies.md",
   "context\\builder\\style.md",
   "context\\builder\\terminal.md",
   "context\\builder\\trade.md",
   "context\\builder\\voice.md",
};

#ifdef __MQL5__
#resource "\\Include\\metatrader-ai\\context\\mql.md" as string FileMQL
#resource "\\Include\\metatrader-ai\\context\\trade.md" as string FileTrade
#resource "\\Include\\metatrader-ai\\context\\prompt.md" as string FilePrompt
#resource "\\Include\\metatrader-ai\\workflows\\response.md" as string FileResponse
//
#resource "\\Include\\metatrader-ai\\context\\builder\\chart.md" as string FileBuilderChart
#resource "\\Include\\metatrader-ai\\context\\builder\\expert-advisor.md" as string FileBuilderExpertAdvisor
#resource "\\Include\\metatrader-ai\\context\\builder\\indicator.md" as string FileBuilderIndicator
#resource "\\Include\\metatrader-ai\\context\\builder\\object.md" as string FileBuilderObject
#resource "\\Include\\metatrader-ai\\context\\builder\\platform.md" as string FileBuilderPlatform
#resource "\\Include\\metatrader-ai\\context\\builder\\risk-management.md" as string FileBuilderRiskManagement
#resource "\\Include\\metatrader-ai\\context\\builder\\script.md" as string FileBuilderScript
#resource "\\Include\\metatrader-ai\\context\\builder\\strategies.md" as string FileBuilderStrategies
#resource "\\Include\\metatrader-ai\\context\\builder\\style.md" as string FileBuilderStyle
#resource "\\Include\\metatrader-ai\\context\\builder\\terminal.md" as string FileBuilderTerminal
#resource "\\Include\\metatrader-ai\\context\\builder\\trade.md" as string FileBuilderTrade
#resource "\\Include\\metatrader-ai\\context\\builder\\voice.md" as string FileBuilderVoice
#else
#import "shell32.dll"
int ShellExecuteW(int hWnd, string lpOperation, string lpFile, string lpParameters, string lpDirectory, int nShowCmd);
#import

#define FILE_COPY(src, dest) (ShellExecuteW(0, "open", "cmd.exe", ("/C copy /Y \"" + src + "\" \"" + dest + "\""), NULL, 0))
#define COMMON_FOLDER TerminalInfoString(TERMINAL_COMMONDATA_PATH) + "\\" + "Files" + "\\"
#endif


//+------------------------------------------------------------------+
//| Read context file                                                |
//+------------------------------------------------------------------+
string contextRead(string path)
{
#ifdef __MQL5__
   if(CONTAINS(path, "context\\mql"))      return FileMQL;
   if(CONTAINS(path, "context\\trade"))    return FileTrade;
   if(CONTAINS(path, "context\\prompt"))   return FilePrompt;
   if(CONTAINS(path, "context\\response")) return FileResponse;
   //
   if(CONTAINS(path, "builder\\indicator")) return FileBuilderIndicator;
   if(CONTAINS(path, "builder\\object")) return FileBuilderObject;
   if(CONTAINS(path, "builder\\platform")) return FileBuilderPlatform;
   if(CONTAINS(path, "builder\\risk-management")) return FileBuilderRiskManagement;
   if(CONTAINS(path, "builder\\script")) return FileBuilderScript;
   if(CONTAINS(path, "builder\\strategies")) return FileBuilderStrategies;
   if(CONTAINS(path, "builder\\style")) return FileBuilderStyle;
   if(CONTAINS(path, "builder\\terminal")) return FileBuilderTerminal;
   if(CONTAINS(path, "builder\\trade")) return FileBuilderTrade;
   if(CONTAINS(path, "builder\\voice")) return FileBuilderVoice;
   return StringFormat("Error: Context file not found for path: %s", path);
#else
   const string ogPath = ::TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Include\\metatrader-ai\\" + path;
   const string commonPath = COMMON_FOLDER + "metatrader-ai\\" + path;
   FILE_COPY(ogPath, commonPath);
   int handle = ::FileOpen("metatrader-ai\\" + path, FILE_READ | FILE_COMMON | FILE_TXT | FILE_ANSI);
   if (handle == INVALID_HANDLE)
   {
      return StringFormat("[Agent] Error '%d', could not open file: %s", GetLastError(), commonPath);
   }
   string content = "";
   while (!::FileIsEnding(handle))
      content += ::FileReadString(handle) + "\n";
   ::FileClose(handle);
   return content;
#endif
}