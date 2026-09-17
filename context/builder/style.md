# MQL Style Guide

## Naming Conventions
- Variables/Functions: camelCase (e.g., `lotSize`, `takeProfit`, `stopLoss`)
- Constants/Enums: UPPER_SNAKE_CASE (e.g., `MAX_RISK_PERCENT`, `MAGIC_NUMBER`)
- Input parameters: camelCase with display labels (e.g., `input double inpRiskPercent = 1.0; // Risk Percent`)

## File Structure
```cpp
//+------------------------------------------------------------------+
//|                                                      example.mq5 |
//|                                           Copyright 2026,Example |
//|                                         https://www.example.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,Example"
#property link      "https://www.example.com/"
#property description "Example Expert Advisor using MQL5"
#property strict

// --- Includes ---
#include <Trade/Trade.mqh>

// --- Inputs ---
input double inpLotSize = 0.1; // Lot Size

// --- Globals ---
int magicNumber = 123456;
CTrade trade;

// --- Event Handlers ---
int OnInit() { return(INIT_SUCCEEDED); }
void OnTick() { }
void OnDeinit(const int reason) { }

// --- Helper Functions ---


// --- Trading Functions ---

```

## Preferred Patterns
- Always use `#property strict` for MQL4 compatibility
- Validate all input parameters in OnInit
- Use `Print()` and `PrintFormat()` for logging, not Comment()
- Check `IsStopped()` before heavy operations
- Always check position/order existence before modifying
- Use `SymbolInfoDouble()` and `SymbolInfoInteger()` for market properties
- Prefer CTrade class (MQL5) over raw OrderSend
- Avoid `Sleep()` in indicators and EAs — use timers or tick-based logic
- Zero-divide checks before all calculations
- ArraySetAsSeries() for time-series arrays in indicators

## Indentation
- 4 spaces (no tabs)
- Opening braces on the next line of the statement
- Single space after `if`, `for`, `while` keywords

## Documentation 
- Brief comment above each function describing purpose
- Inline comments only for non-obvious logic
- No emojis in code comments, docstrings, or tkinter/customtkinter apps.
- No long decorative separators `──────────────────────────────────────────────` unless specifically needed for MQL code structure.
- If comments are used, they should be 3-5 words max. 
- Instead of `# ── Header ──` do `# Header` 
- Always use function docstrings when creating or editing Python functions. Docstrings should be concise, describing the function's purpose and all parameters/returns in 1-3 sentences.
- All user-facing messages should be concise and practical, without flowery language or emojis.

## Error Handling
- Always check return values of trade operations
- Use `GetLastError()` after failed operations
- Reset error with `ResetLastError()` before critical calls
- Log errors with `PrintFormat("Error %d in FuncName: ...", GetLastError())`
