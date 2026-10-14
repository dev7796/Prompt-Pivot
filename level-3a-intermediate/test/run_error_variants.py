"""Addendum: find a question where the instructive error actually drives a retry (scene errors)."""
import json, os, anthropic
client = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=6)
MODEL = "us.anthropic.claude-opus-5-5"
TOOLS = [{"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
          "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}]
def get_weather_strict(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12, "san francisco, ca": 15}
    if city.lower() not in fake_db:
        raise ValueError("City not found. Try the full name with region, e.g. 'San Francisco, CA'")
    return f"{fake_db[city.lower()]} C"
def run(q):
    trace=[]; messages=[{"role":"user","content":q}]
    for step in range(6):
        r=client.messages.create(model=MODEL,max_tokens=1024,system="You are a weather assistant. Use tools for live data.",tools=TOOLS,messages=messages)
        messages.append({"role":"assistant","content":r.content})
        if r.stop_reason!="tool_use": return trace,"".join(b.text for b in r.content if b.type=="text")
        res=[]
        for b in r.content:
            if b.type!="tool_use": continue
            trace.append(f"[step {step}] {b.name}({b.input})")
            try: res.append({"type":"tool_result","tool_use_id":b.id,"content":get_weather_strict(**b.input)})
            except Exception as e:
                trace.append(f"[step {step}]   -> Error: {e}"); res.append({"type":"tool_result","tool_use_id":b.id,"content":f"Error: {e}","is_error":True})
        messages.append({"role":"user","content":res})
    return trace,"max steps"
out={}
for q in ["What's the weather in SF?", "What's the weather in San Francisco?", "How warm is it in Lyon right now?"]:
    t,a=run(q); out[q]={"trace":t,"answer":a}; print("\n==",q); print("\n".join(t)); print("->",a[:300])
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"results_error_variants.json"),"w"),indent=1)
