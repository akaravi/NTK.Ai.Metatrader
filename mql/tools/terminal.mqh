//+------------------------------------------------------------------+
//|                                                     terminal.mqh |
//|                                      Copyright 2026,JBlanked LLC |
//|                                         https://www.jblanked.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked LLC"
#property link      "https://www.jblanked.com"
#property strict

#include "JSON.mqh"

// forwards (in mql4 is shows import warning)
#ifdef __MQL5__
string getTerminalInfo();
#endif

//+------------------------------------------------------------------+
//| Get common information about the current MetaTrader terminal     |
//+------------------------------------------------------------------+
string getTerminalInfo()
{
   CJAVal result;
   result["name"]         = MQLInfoString(MQL_PROGRAM_NAME);  // name of the launched MQL5 program
   result["path"]         = MQLInfoString(MQL_PROGRAM_PATH);  // running program path

   result["program_memory_limit"] = MQLInfoInteger(MQL_MEMORY_LIMIT); // maximum possible amount of dynamic memory for MQL5 program in MB
   result["program_memory_used"]  = MQLInfoInteger(MQL_MEMORY_USED);  // memory size used by MQL5 program in MB

   result["os_ver"] = TerminalInfoString(TERMINAL_OS_VERSION);      // user's OS
   result["name"]   = TerminalInfoString(TERMINAL_NAME);            // terminal name
   result["path"]   = TerminalInfoString(TERMINAL_PATH);            // folder the terminal is launched from
   result["data"]   = TerminalInfoString(TERMINAL_DATA_PATH);       // folder for storing the terminal data
   result["common"] = TerminalInfoString(TERMINAL_COMMONDATA_PATH); // common folder for all client terminals installed on the computer
   result["cpu"]    = TerminalInfoString(TERMINAL_CPU_NAME);        // cpu name

   result["disk_space"]    = TerminalInfoInteger(TERMINAL_DISK_SPACE);          // Free disk space for the MQL5\Files folder of the terminal (agent), MB
   result["cores"]         = TerminalInfoInteger(TERMINAL_CPU_CORES);           // The number of CPU cores in the system
   result["build"]         = TerminalInfoInteger(TERMINAL_BUILD);               // The client terminal build number
   result["is_x64"]        = (bool)TerminalInfoInteger(TERMINAL_X64);           // Indication of the "64-bit terminal"
   result["connected"]     = (bool)TerminalInfoInteger(TERMINAL_CONNECTED);     // if trade server is connected
   result["trade_allowed"] = (bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED); // Permission to trade
   result["ping_last"]     = TerminalInfoInteger(TERMINAL_PING_LAST);           // The last known value of a ping to a trade server in microseconds. One second comprises of one million microseconds
   result["width"]         = TerminalInfoInteger(TERMINAL_SCREEN_WIDTH);        // terminal width
   result["height"]        = TerminalInfoInteger(TERMINAL_SCREEN_HEIGHT);       // terminal height

   result["terminal_memory_total"]     = TerminalInfoInteger(TERMINAL_MEMORY_TOTAL);     // Memory available to the process of the terminal (agent), MB
   result["terminal_memory_available"] = TerminalInfoInteger(TERMINAL_MEMORY_AVAILABLE); // Free memory of the terminal (agent) process, MB
   result["terminal_memory_used"]      = TerminalInfoInteger(TERMINAL_MEMORY_USED);      // Memory used by the terminal (agent), MB

   result["community_balance"] = TerminalInfoDouble(TERMINAL_COMMUNITY_BALANCE); // Balance in MQL5.community
   return result.Serialize();
}
//+------------------------------------------------------------------+
