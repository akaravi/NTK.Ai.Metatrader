# MQL Chart Object Operations

## Object Creation
```cpp
// Horizontal line
ObjectCreate(0, "hline1", OBJ_HLINE, 0, 0, price);

// Trend line
ObjectCreate(0, "trend1", OBJ_TREND, 0, time1, price1, time2, price2);

// Rectangle
ObjectCreate(0, "rect1", OBJ_RECTANGLE, 0, time1, price1, time2, price2);

// Fibonacci retracement
ObjectCreate(0, "fib1", OBJ_FIBO, 0, time1, price1, time2, price2);

// Text label
ObjectCreate(0, "label1", OBJ_LABEL, 0, 0, 0);
ObjectSetInteger(0, "label1", OBJPROP_XDISTANCE, 10);
ObjectSetInteger(0, "label1", OBJPROP_YDISTANCE, 20);
ObjectSetString(0, "label1", OBJPROP_TEXT, "My Label");

// Arrow
ObjectCreate(0, "arrow1", OBJ_ARROW, 0, time, price);

// Button (MQL5 only)
ObjectCreate(0, "btn1", OBJ_BUTTON, 0, 0, 0);
ObjectSetInteger(0, "btn1", OBJPROP_XDISTANCE, 10);
ObjectSetInteger(0, "btn1", OBJPROP_YDISTANCE, 50);
ObjectSetInteger(0, "btn1", OBJPROP_XSIZE, 100);
ObjectSetInteger(0, "btn1", OBJPROP_YSIZE, 30);
```

## Object Properties
```cpp
// Set color
ObjectSetInteger(0, name, OBJPROP_COLOR, clrBlue);

// Set line style
ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_SOLID);
ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DASH);
ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DOT);

// Set line width
ObjectSetInteger(0, name, OBJPROP_WIDTH, 2);

// Set ray (extend line right)
ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT, true);

// Set text properties
ObjectSetString(0, name, OBJPROP_TEXT, "text");
ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 10);
ObjectSetString(0, name, OBJPROP_FONT, "Arial");

// Set anchor point
ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_LEFT);

// Time/price coordinates
ObjectSetInteger(0, name, OBJPROP_TIME, 0, time);  // second point
ObjectSetDouble(0, name, OBJPROP_PRICE, 0, price);
```

## Object Deletion
```cpp
// Delete single object
ObjectDelete(0, name);

// Delete by prefix
void DeleteObjectsByPrefix(string prefix) {
    int total = ObjectsTotal(0);
    for (int i = total - 1; i >= 0; i--) {
        string name = ObjectName(0, i);
        if (StringFind(name, prefix) == 0)
            ObjectDelete(0, name);
    }
}

// Delete all objects on chart
ObjectsDeleteAll(0);

// Delete by type
ObjectsDeleteAll(0, OBJ_HLINE);
```

## Object Detection
```cpp
// Check if object exists
if (ObjectFind(0, name) >= 0) { /* exists */ }

// Get object properties
double price = ObjectGetDouble(0, name, OBJPROP_PRICE);
datetime time = (datetime)ObjectGetInteger(0, name, OBJPROP_TIME);
color clr = (color)ObjectGetInteger(0, name, OBJPROP_COLOR);
string text = ObjectGetString(0, name, OBJPROP_TEXT);

// Get total objects on chart
int total = ObjectsTotal(0);

// Get object name by index
string objName = ObjectName(0, index);

// Get object type
ENUM_OBJECT type = (ENUM_OBJECT)ObjectGetInteger(0, name, OBJPROP_TYPE);
```

## Common Object Types
| Constant | Object |
|----------|--------|
| OBJ_VLINE | Vertical line |
| OBJ_HLINE | Horizontal line |
| OBJ_TREND | Trend line |
| OBJ_TRENDBYANGLE | Trend by angle |
| OBJ_CYCLES | Cycle lines |
| OBJ_ARROWED_LINE | Arrowed line |
| OBJ_CHANNEL | Equidistant channel |
| OBJ_STDDEVCHANNEL | Standard deviation channel |
| OBJ_REGRESSION | Linear regression |
| OBJ_PITCHFORK | Andrews pitchfork |
| OBJ_GANNLINE | Gann line |
| OBJ_GANNFAN | Gann fan |
| OBJ_GANNGRID | Gann grid |
| OBJ_FIBO | Fibonacci retracement |
| OBJ_FIBOTIMES | Fibonacci time zones |
| OBJ_FIBOFAN | Fibonacci fan |
| OBJ_FIBOARC | Fibonacci arc |
| OBJ_FIBOCHANNEL | Fibonacci channel |
| OBJ_EXPANSION | Fibonacci expansion |
| OBJ_RECTANGLE | Rectangle |
| OBJ_TRIANGLE | Triangle |
| OBJ_ELLIPSE | Ellipse |
| OBJ_ARROW_THUMB_UP | Thumb up |
| OBJ_ARROW_THUMB_DOWN | Thumb down |
| OBJ_ARROW | Arrow |
| OBJ_TEXT | Text |
| OBJ_LABEL | Text label |
| OBJ_BUTTON | Button |
| OBJ_EDIT | Edit field |

## Color Constants
```cpp
clrBlack, clrWhite, clrRed, clrGreen, clrBlue, clrYellow,
clrCyan, clrMagenta, clrOrange, clrLime, clrGray, clrDimGray,
clrDarkGray, clrLightGray, clrNavy, clrMaroon, clrPurple,
clrOlive, clrTeal, clrSilver, clrGold, clrPink, clrCoral,
clrSalmon, clrTomato, clrLightBlue, clrLightCyan, clrLightGreen,
clrLightYellow, clrLightPink, clrLightSalmon, clrDarkBlue,
clrDarkGreen, clrDarkRed, clrDarkCyan, clrDarkMagenta,
clrDarkOrange, clrDarkViolet
```
