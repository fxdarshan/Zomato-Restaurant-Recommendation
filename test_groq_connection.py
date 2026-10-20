import os, time, groq

env_path = r'C:\Users\DARSHAN\Documents\BitbyBit\AI\01 Build Hour Restaurants Recommendation like Zomato\.env'
api_key = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('GROQ_API_KEY='): api_key = line.split('=',1)[1].strip()

MODEL = 'qwen/qwen3.8-27b'
print(f'=== Groq API Connection Test ===')
print(f'Key  : {api_key[:8]}...{api_key[-4:]}')
print(f'Model: {MODEL}')
print('Making one API call...')

t = time.perf_counter()
r = groq.Groq(api_key=api_key).chat.completions.create(
    model=MODEL,
    messages=[{'role':'user', 'content': 'Reply with only valid JSON: {"status": "connected"}'}],
    response_format={'type': 'json_object'},
    temperature=0.0,
    max_tokens=20,
)
latency = round(time.perf_counter() - t, 3)

print(f'Response: {r.choices[0].message.content}')
print(f'Tokens  : {r.usage.total_tokens}')
print(f'Latency : {latency}s')
print()
print('GROQ CONNECTION: OK')
