//+------------------------------------------------------------------+
//|                                                  backtesting.mqh |
//|                                      Copyright 2026,JBlanked LLC |
//|                                         https://www.jblanked.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked LLC"
#property link      "https://www.jblanked.com"
#property strict

#include "JSON.mqh"
#include "JB-Backtest.mqh"

// forwards (in mql4 is shows import warning)
#ifdef __MQL5__
string backtestOptimization(CJAVal &testInputs, CJAVal &optimizationParams);
string backtestSingle(CJAVal &testInputs, CJAVal &expertParams);
#endif

/*
- Test Inputs
  - name
  - symbol
  - timeframe
  - to_date
  - from_date
  - deposit
- Expert Params (array)
  - key
  - value
  - type (string, bool, double, int)
- Optimization params (array)
  - key
  - value
  - start_value
  - step_value
  - stop_value
  - checked (bool)
  - type (string, bool, double, int)
*/

//+------------------------------------------------------------------+
//| Run an optimization in the strategy tester                       |
//+------------------------------------------------------------------+
string backtestOptimization(CJAVal &testInputs, CJAVal &optimizationParams)
{
   testerInputs inputs;
   inputs.expertName            = testInputs["name"].ToStr(); // expert advisor name
   inputs.optimization          = true;                       // optimization on

   if(testInputs["symbol"].ToStr() != "")
      inputs.symbol = testInputs["symbol"].ToStr(); // currency pair

   if(testInputs["timeframe"].ToStr() != "")
      inputs.timeFrame = (ENUM_TIMEFRAMES)testInputs["timeframe"].ToInt(); // timeframe to test (PERIOD_xxx);

   if(testInputs["to_date"].ToStr() != "")
      inputs.toDate = (datetime)testInputs["to_date"].ToStr(); // start date

   if(testInputs["from_date"].ToStr() != "")
      inputs.fromDate = (datetime)testInputs["from_date"].ToStr(); // end date
   
   if(testInputs["deposit"].ToStr() != "")
      inputs.deposit = testInputs["deposit"].ToDbl(); // starting balance to test

   CBacktest test(inputs);
   const int listSize = ArraySize(optimizationParams.m_e);
   string paramType = "";
   for (int i = 0; i < listSize; i++)
   {
      paramType = optimizationParams[i]["type"].ToStr();
      if(paramType == "string")
      {
         test.addSetting(optimizationParams[i]["key"].ToStr(), optimizationParams[i]["value"].ToStr());
      }
      else if(paramType == "int")
      {
         test.addOptimizationSetting(optimizationParams[i]["key"].ToStr(), IntegerToString(optimizationParams[i]["value"].ToInt()), IntegerToString(optimizationParams[i]["start_value"].ToInt()), IntegerToString(optimizationParams[i]["step_value"].ToInt()), IntegerToString(optimizationParams[i]["stop_value"].ToInt()), optimizationParams[i]["checked"].ToBool());
      }
      else if(paramType == "double")
      {
         test.addOptimizationSetting(optimizationParams[i]["key"].ToStr(), test.doubleToString(optimizationParams[i]["value"].ToDbl()), test.doubleToString(optimizationParams[i]["start_value"].ToDbl()), test.doubleToString(optimizationParams[i]["step_value"].ToDbl()), test.doubleToString(optimizationParams[i]["stop_value"].ToDbl()), optimizationParams[i]["checked"].ToBool());
      }
      else if(paramType == "bool")
      {
         test.addOptimizationSetting(optimizationParams[i]["key"].ToStr(), (string)optimizationParams[i]["value"].ToBool(), (string)optimizationParams[i]["start_value"].ToBool(), (string)optimizationParams[i]["step_value"].ToBool(), (string)optimizationParams[i]["stop_value"].ToBool(), optimizationParams[i]["checked"].ToBool());
      }
      else
      {
         test.addOptimizationSetting(optimizationParams[i]["key"].ToStr(), optimizationParams[i]["value"].ToStr(), optimizationParams[i]["start_value"].ToStr(), optimizationParams[i]["step_value"].ToStr(), optimizationParams[i]["stop_value"].ToStr(), optimizationParams[i]["checked"].ToBool());
      }
   }

   return test.run();
}

//+------------------------------------------------------------------+
//| Run a single test in the strategy tester                         |
//+------------------------------------------------------------------+
string backtestSingle(CJAVal &testInputs, CJAVal &expertParams)
{
   testerInputs inputs;
   inputs.expertName            = testInputs["name"].ToStr(); // expert advisor name

   if(testInputs["symbol"].ToStr() != "")
      inputs.symbol = testInputs["symbol"].ToStr(); // currency pair

   if(testInputs["timeframe"].ToStr() != "")
      inputs.timeFrame = (ENUM_TIMEFRAMES)testInputs["timeframe"].ToInt(); // timeframe to test (PERIOD_xxx);

   if(testInputs["to_date"].ToStr() != "")
      inputs.toDate = (datetime)testInputs["to_date"].ToStr(); // start date

   if(testInputs["from_date"].ToStr() != "")
      inputs.fromDate = (datetime)testInputs["from_date"].ToStr(); // end date
   
   if(testInputs["deposit"].ToStr() != "")
      inputs.deposit = testInputs["deposit"].ToDbl(); // starting balance to test              

   CBacktest test(inputs);
   const int listSize = ArraySize(expertParams.m_e);
   string paramType = "";
   for (int i = 0; i < listSize; i++)
   {
      paramType = expertParams[i]["type"].ToStr();
      if(paramType == "string")
      {
         test.addSetting(expertParams[i]["key"].ToStr(), expertParams[i]["value"].ToStr());
      }
      else if(paramType == "int")
      {
         test.addSetting(expertParams[i]["key"].ToStr(), IntegerToString(expertParams[i]["value"].ToInt()));
      }
      else if(paramType == "double")
      {
         test.addSetting(expertParams[i]["key"].ToStr(), test.doubleToString(expertParams[i]["value"].ToDbl()));
      }
      else if(paramType == "bool")
      {
         test.addSetting(expertParams[i]["key"].ToStr(), (string)expertParams[i]["value"].ToBool());
      }
      else
      {
         test.addSetting(expertParams[i]["key"].ToStr(), expertParams[i]["value"].ToStr());
      }
   }

   return test.run();
}
//+------------------------------------------------------------------+
