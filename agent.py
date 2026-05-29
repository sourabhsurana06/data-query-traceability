
import os
from unittest import result
from os import path, listdir, getenv, getcwd
from dotenv import load_dotenv
load_dotenv()

import duckdb, json
from openai import OpenAI

print(os.path.exists(".env"))
os.listdir()
print("cwd:", os.getcwd())
print("key:", os.getenv("OPENAI_API_KEY"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-5-mini"
MAX_TURNS = 8

SCHEMA_HINT = """Table: sales
Columns: week (1-8), category, region, units, asp (avg selling price), revenue.
One row per week x category x region."""

def run_sql(query: str) -> str:
    try:
        con = duckdb.connect("retail.db", read_only=True)
        df = con.execute(query).df()
        con.close()
        return df.to_string(index=False) if len(df) else "(no rows)"
    except Exception as e:
        return f"SQL ERROR: {e}"

tools = [{
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": f"Run a read-only SQL query on the retail database. {SCHEMA_HINT}",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}]

SYSTEM = """You are a retail analytics agent. Your job is to answer the question by querying data.
RULES:
0. EXPLAIN YOUR THINKING. Include your thought process to show how you are interpreting the question and the data.
1. Start by running SQL queries to examine the data relevant to the question.
2. After each query result, interpret what you learned and decide what to query next.
3. STOP QUERYING when you have identified the root cause or key drivers. Do not keep drilling deeper looking for "more information."
4. Once you have enough evidence, state a clear headline conclusion FIRST, then show the supporting data.
5. Never claim something happened unless you verified it with a query result.
6. Lead with the single most important finding. Do not give equal weight to minor variations and critical issues.
"""

import pandas as pd
import json

trace = []

def run_agent(question):
    trace.clear()  # list of dicts, one per turn
    
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    
    for turn in range(MAX_TURNS):
        print(f"\n{'='*60}\n  TURN {turn}\n{'='*60}")
        
        # Capture what's being sent to the LLM
        messages_sent = json.dumps(messages, indent=2, default=str)
        
        # Call the LLM
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools,temperature=1) 
        msg = resp.choices[0].message
        messages.append(msg)
        
        # Extract what the model returned
        assistant_thinking = msg.content or "[no thinking text]"
        tool_calls_made = []
        
        if msg.content:
            print(f"[thinking]\n{msg.content}")

        if not msg.tool_calls:
            # Agent is done — capture final turn and return
            trace.append({
                "turn": turn,
                "model": MODEL,
                "messages_sent": messages_sent,
                "assistant_response": assistant_thinking,
                "tool_calls": None,
                "sql_queries": None,
                "sql_results": None,
            })
            
            # Convert trace to DataFrame and save
            df_trace = pd.DataFrame(trace)
            df_trace.to_csv("agent_trace.csv", index=False)
            print("\n[saved trace to agent_trace.csv]")
            return assistant_thinking

        # Process tool calls
        sql_queries = []
        sql_results = []
        
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            query = args["query"]
            sql_queries.append(query)
            
            print(f"\n[turn {turn}] SQL:\n{query}")
            result = run_sql(query)
            sql_results.append(result)
            print(f"[result]\n{result}")
            
            tool_calls_made.append({
                "tool_name": call.function.name,
                "tool_id": call.id,
                "query": query,
            })
            
            # Append the tool result to messages for next turn
            messages.append({"role": "tool",
                             "tool_call_id": call.id,
                             "content": result})
        
        # Record this turn's trace
        trace.append({
            "turn": turn,
            "model": MODEL,
            "messages_sent": messages_sent,
            "assistant_response": assistant_thinking,
            "tool_calls": json.dumps(tool_calls_made),
            "sql_queries": " | ".join(sql_queries),
            "sql_results": " | ".join(sql_results),
        })

    return "Hit MAX_TURNS without finishing."


q = "Whats the lift in my total revenue between week 7 and 8. Is there a downward trend? What's causing this downward trend? Investigate."
answer = run_agent(q)
print(f"\n{'='*60}\n  FINAL ANSWER\n{'='*60}\n{answer}")

type(trace)

t = pd.DataFrame(trace)
t
with open("df.csv","w") as f:
    f.write(t.to_csv(index=False))

with open("output.txt", "w") as f:
    f.write(answer)
print("\n[saved to output.txt]")

for h in resp1:
    for i in resp1[h]["choices"][0]:
        print(i)


for h in resp1:
    print(f"\n{'='*60}\n  {h["choices"][0].message} \n{'='*60}")