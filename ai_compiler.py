import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from schema import BakeryOperationalTarget

# Load environment variables from .env file
load_dotenv()

SYSTEM_INSTRUCTION = """
You are an expert operational intent compiler for PanaderyaOptimizer, a system designed for Filipino community bakeries.
Your sole job is to translate conversational Taglish (Tagalog-English code-switched) user prompts into a structured JSON representation of operational goals and constraints.

CRITICAL RULES:
1. Do NOT perform any mathematical calculations, profit estimates, or tray allocations. Focus strictly on extracting user intentions, stated targets, and explicit constraints.
2. Parse product names accurately (e.g., "Pan de Sal", "Spanish Bread", "Ensaymada", "Cheese Bread").
3. Identify target demands, clearance deadlines, minimum acceptable margin goals, and operational roles when mentioned.
4. Extract explicit monetary targets (e.g., target net profit in PHP) or oven capacity constraints if provided by the baker.
5. You must return structured output adhering strictly to the provided JSON schema.
"""


def get_genai_client() -> genai.Client:
    """Instantiates and returns the Google GenAI SDK client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing in .env file.")
    return genai.Client(api_key=api_key)


def compile_taglish_intent(user_prompt: str) -> BakeryOperationalTarget:
    """
    Ingests a Taglish conversational prompt from a baker, calls Gemini API
    with Pydantic schema enforcement, and returns a validated BakeryOperationalTarget object.
    
    Rule C.4.c Compliant: Isolates AI strictly to semantic translation and data ingestion.
    """
    client = get_genai_client()

    response = client.models.generate_content(
        model="gemini-3.8-flash",  # Updated to gemini-3.8-flash
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=BakeryOperationalTarget,
            temperature=0.1,  # Low temperature for deterministic, reliable parsing
        ),
    )

    # Return the Pydantic-validated output object directly from the response SDK
    parsed_target: BakeryOperationalTarget = response.parsed
    return parsed_target


if __name__ == "__main__":
    # Test execution with example Taglish prompt
    test_prompt = (
        "Gusto ko maubos ang Spanish bread bago mag-4 PM kahit breakeven lang, "
        "pero dapat umabot sa ₱1,200 ang net profit gamit ang Ensaymada at Cheese Bread. "
        "Max 10 trays lang kasya sa oven ko."
    )
    print("Parsing sample Taglish prompt:")
    print(f"'{test_prompt}'\n")

    try:
        compiled_target = compile_taglish_intent(test_prompt)
        print("--- AI COMPILER EXTRACTED STRUCTURED TARGET ---")
        print(compiled_target.model_dump_json(indent=2))
        print("-----------------------------------------------")
    except Exception as e:
        print(f"Error compiling prompt: {e}")