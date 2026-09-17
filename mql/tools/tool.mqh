//+------------------------------------------------------------------+
//|                                                         tool.mqh |
//|                                          Copyright 2026,JBlanked |
//|                                        https://www.jblanked.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked"
#property link      "https://www.jblanked.com/"
#property strict

#include "JSON.mqh"

//+------------------------------------------------------------------+
//| Property — describes a single property of a tool                 |
//+------------------------------------------------------------------+
class Property
{
public:
   string name;
   string type;
   string description;
   bool   required;

   Property(string p_name, string p_type, string p_description, bool p_required = false)
   {
      name        = p_name;
      type        = p_type;
      description = p_description;
      required    = p_required;
   }

   void json(CJAVal &out)
   {
      out["type"]        = type;
      out["description"] = description;
   }
};

//+------------------------------------------------------------------+
//| Parameters — collection of properties for a tool's input schema  |
//+------------------------------------------------------------------+
class Parameters
{
public:
   Property *properties[];   // array of pointers
   int       count;

   Parameters()
   {
      count = 0;
      ArrayResize(properties, 0);
   }

   // Add a property (takes ownership of the pointer)
   void add(Property *prop)
   {
      int n = ArrayResize(properties, count + 1);
      properties[count] = prop;
      count++;
   }

   void json(CJAVal &out)
   {
      out["type"] = "object";

      // Build the "properties" object
      CJAVal props;
      props.m_type = jtOBJ;
      for (int i = 0; i < count; i++)
      {
         CJAVal prop;
         properties[i].json(prop);
         props[properties[i].name].Set(prop);
      }
      out["properties"].Set(props);

      // Build the "required" array (only if at least one property is required)
      CJAVal req;
      req.m_type = jtARRAY;
      int reqCount = 0;
      for (int i = 0; i < count; i++)
      {
         if (properties[i].required)
         {
            req.Add(properties[i].name);
            reqCount++;
         }
      }
      if (reqCount > 0)
      {
         out["required"].Set(req);
      }
   }

   ~Parameters()
   {
      for (int i = 0; i < count; i++)
      {
         if (CheckPointer(properties[i]) == POINTER_DYNAMIC)
            delete properties[i];
      }
      ArrayResize(properties, 0);
   }
};

//+------------------------------------------------------------------+
//| Tool - represents a tool with a name, description, and parameters|
//+------------------------------------------------------------------+
class Tool
{
public:
   string      name;
   string      description;
   Parameters *parameters;

   Tool(string p_name, string p_description, Parameters *p_parameters = NULL)
   {
      name        = p_name;
      description = p_description;
      parameters  = p_parameters;
   }

   virtual string execute(CJAVal &json)
   {
      return "{\"error\":\"not implemented\"}";
   }

   void json_anthropic(CJAVal &out)
   {
      out["name"]        = name;
      out["description"] = description;

      CJAVal schema;
      if (parameters != NULL)
      {
         parameters.json(schema);
      }
      else
      {
         schema["type"] = "object";
         CJAVal emptyProps;
         emptyProps.m_type = jtOBJ;
         schema["properties"].Set(emptyProps);
      }
      out["input_schema"].Set(schema);
   }

   void json_openai(CJAVal &out)
   {
      out["type"] = "function";

      CJAVal func;
      func["name"]        = name;
      func["description"] = description;

      CJAVal schema;
      if (parameters != NULL)
      {
         parameters.json(schema);
      }
      else
      {
         schema["type"] = "object";
         CJAVal emptyProps;
         emptyProps.m_type = jtOBJ;
         schema["properties"].Set(emptyProps);
      }
      func["parameters"].Set(schema);
      out["function"].Set(func);
   }

   ~Tool()
   {
      if (parameters != NULL && CheckPointer(parameters) == POINTER_DYNAMIC)
         delete parameters;
   }
};
//+------------------------------------------------------------------+
