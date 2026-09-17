# MQL Terminal Operations

## Terminal Information
```cpp
// Terminal status
bool isConnected = TerminalInfoInteger(TERMINAL_CONNECTED);
bool tradeAllowed = TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);
bool dllAllowed = TerminalInfoInteger(TERMINAL_DLLS_ALLOWED);
bool emailEnabled = TerminalInfoInteger(TERMINAL_EMAIL_ENABLED);
bool ftpEnabled = TerminalInfoInteger(TERMINAL_FTP_ENABLED);

// Terminal paths
string dataPath = TerminalInfoString(TERMINAL_DATA_PATH);
string commonPath = TerminalInfoString(TERMINAL_COMMONDATA_PATH);
string exePath = TerminalInfoString(TERMINAL_PATH);

// Terminal properties
string terminalName = TerminalInfoString(TERMINAL_NAME);
string terminalCompany = TerminalInfoString(TERMINAL_COMPANY);
int buildNumber = (int)TerminalInfoInteger(TERMINAL_BUILD);
int maxBars = (int)TerminalInfoInteger(TERMINAL_MAXBARS);
int cpuCores = (int)TerminalInfoInteger(TERMINAL_CPU_CORES);

// Memory info
int physicalMemory = (int)TerminalInfoInteger(TERMINAL_MEMORY_PHYSICAL);
int availableMemory = (int)TerminalInfoInteger(TERMINAL_MEMORY_AVAILABLE);
int usedMemory = (int)TerminalInfoInteger(TERMINAL_MEMORY_USED);

// Language
int language = (int)TerminalInfoInteger(TERMINAL_LANGUAGE);
string langStr;
switch(language) {
    case 0x0449: langStr = "Russian"; break;
    case 0x0409: langStr = "English"; break;
    default: langStr = "Other";
}
```

## Account Information
```cpp
double balance = AccountInfoDouble(ACCOUNT_BALANCE);
double equity = AccountInfoDouble(ACCOUNT_EQUITY);
double profit = AccountInfoDouble(ACCOUNT_PROFIT);
double margin = AccountInfoDouble(ACCOUNT_MARGIN);
double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
double marginLevel = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
int leverage = (int)AccountInfoInteger(ACCOUNT_LEVERAGE);

// Account details
string accountName = AccountInfoString(ACCOUNT_NAME);
string accountServer = AccountInfoString(ACCOUNT_SERVER);
string accountCurrency = AccountInfoString(ACCOUNT_CURRENCY);
long accountNumber = AccountInfoInteger(ACCOUNT_LOGIN);
bool isTradeAllowed = AccountInfoInteger(ACCOUNT_TRADE_ALLOWED);
bool isEAAllowed = AccountInfoInteger(ACCOUNT_TRADE_EXPERT);
ENUM_ACCOUNT_TRADE_MODE tradeMode = (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);

// Account type
string accountType;
switch(tradeMode) {
    case ACCOUNT_TRADE_MODE_DEMO: accountType = "Demo"; break;
    case ACCOUNT_TRADE_MODE_CONTEST: accountType = "Contest"; break;
    case ACCOUNT_TRADE_MODE_REAL: accountType = "Real"; break;
    default: accountType = "Unknown";
}

// Account stop out
int stopOutMode = (int)AccountInfoInteger(ACCOUNT_MARGIN_SO_MODE);
double stopOutLevel = AccountInfoDouble(ACCOUNT_MARGIN_SO_CALL);
double stopOutExit = AccountInfoDouble(ACCOUNT_MARGIN_SO_SO);
```

## Symbol/Market Information
```cpp
double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * point;
double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
double contractSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);

// Symbol status
bool isMarketOpen = (bool)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
bool isFrozen = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL) > 0;
double swapLong = SymbolInfoDouble(_Symbol, SYMBOL_SWAP_LONG);
double swapShort = SymbolInfoDouble(_Symbol, SYMBOL_SWAP_SHORT);
int swap3Day = (int)SymbolInfoInteger(_Symbol, SYMBOL_SWAP_MODE);

// Symbol description
string symbolDesc = SymbolInfoString(_Symbol, SYMBOL_DESCRIPTION);
string symbolCurrencyBase = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_BASE);
string symbolCurrencyProfit = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT);
string symbolPath = SymbolInfoString(_Symbol, SYMBOL_PATH);

// Symbol session times
datetime sessionOpen, sessionClose;
SymbolInfoSessionQuote(_Symbol, MONDAY, 0, sessionOpen, sessionClose);
SymbolInfoSessionTrade(_Symbol, MONDAY, 0, sessionOpen, sessionClose);
```

## Global Variables
```cpp
// Set global var
GlobalVariableSet("MyVar_Count", 10);
GlobalVariableSet("MyVar_Price", 1.2345);

// Get global variable
double count = GlobalVariableGet("MyVar_Count");
if (!GlobalVariableCheck("MyVar_Count")) {
    // Variable doesn't exist
}

// Delete global variable
GlobalVariableDel("MyVar_Count");
GlobalVariablesDeleteAll("MyVar_");  // Delete all with prefix

// Temp global var
GlobalVariableTemp("TempVar", 5.0);

// Client terminal global
GlobalVariableSetOnCondition("MyVar", newValue, expectedOldValue);
```

## Email & Notifications
```cpp
// Send push
SendNotification("Trade opened: EURUSD Buy " + DoubleToString(lotSize, 2));

// Send email
SendMail("Trade Alert", "New trade opened on EURUSD");

// Play sound
PlaySound("alert.wav");
PlaySound("expert.wav");
PlaySound("ok.wav");
```

## Sleep & Timing
```cpp
// Scripts only
Sleep(1000);

// Use timer in EAs
uint startTime = GetTickCount();
// ... operation ...
uint elapsed = GetTickCount() - startTime;  // Milliseconds

// Time functions
datetime serverTime = TimeCurrent();   // Last known server time
datetime localTime = TimeLocal();      // Local computer time
datetime gmtTime = TimeGMT();          // GMT time
```

## File Operations
```cpp
// Write to file
int handle = FileOpen("data.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ",");
FileWrite(handle, "Time", "Price", "Volume");
FileClose(handle);

// Read from file
handle = FileOpen("data.csv", FILE_READ | FILE_CSV | FILE_ANSI, ",");
while (!FileIsEnding(handle)) {
    string row = FileReadString(handle);
}
FileClose(handle);

// Common folders
string terminalPath = TerminalInfoString(TERMINAL_PATH);
string dataPath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\";
string commonPath = TerminalInfoString(TERMINAL_COMMONDATA_PATH) + "\\Files\\";

// Use FILE_COMMON for shared access
handle = FileOpen("shared.csv", FILE_WRITE | FILE_CSV | FILE_COMMON);
```
