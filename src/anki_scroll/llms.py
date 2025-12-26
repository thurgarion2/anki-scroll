from dotenv import load_dotenv
import dspy
load_dotenv()

def _open_router(model: str):
    return f"openrouter/{model}"

grok_fast = dspy.LM(_open_router("x-ai/grok-4.1-fast"))
grok_fast_no_cache = dspy.LM(_open_router("x-ai/grok-4.1-fast"), cache=False)
oss_120 = dspy.LM(_open_router("openai/gpt-oss-120b"), temperature= 1.0)