import os
import json
import time
import random
import logging
import httpx
from datetime import datetime
from pydantic import ValidationError
from openai import OpenAI, APIStatusError, APITimeoutError
from fastapi import HTTPException
from src.llm.schema import TaskEnrichmentResponse, CategoryEnum, UrgencyEnum

# Set up logging for cost
cost_logger = logging.getLogger("cost_logger")
cost_logger.setLevel(logging.INFO)
cost_handler = logging.StreamHandler()
cost_handler.setFormatter(logging.Formatter('%(message)s'))
cost_logger.addHandler(cost_handler)

# Set up quarantine logging
os.makedirs("logs", exist_ok=True)
quarantine_logger = logging.getLogger("quarantine_logger")
quarantine_logger.setLevel(logging.INFO)
quarantine_handler = logging.FileHandler("logs/quarantine.jsonl")
quarantine_handler.setFormatter(logging.Formatter('%(message)s'))
quarantine_logger.addHandler(quarantine_handler)

def load_prompt():
    with open("prompts/task-enricher-v1.md", "r") as f:
        return f.read()

def clean_json_response(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def call_model_with_retry(client, model, messages, is_repair=False):
    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries):
        start_time = time.time()
        try:
            res = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log cost
            cost_logger.info(json.dumps({
                "prompt_version": "v1",
                "model": model,
                "input_tokens": res.usage.prompt_tokens if res.usage else 0,
                "output_tokens": res.usage.completion_tokens if res.usage else 0,
                "duration_ms": duration_ms,
                "repair_needed": is_repair
            }))
            
            return res.choices[0].message.content
            
        except (APIStatusError, APITimeoutError) as e:
            # Don't retry on 400, 401, 403
            if isinstance(e, APIStatusError) and e.status_code in [400, 401, 403]:
                raise e
            
            # Retry on 429 and 5xx and timeouts
            if attempt == max_retries - 1:
                raise e
                
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            # Obey Retry-After if present
            if hasattr(e, 'response') and e.response is not None:
                retry_after = e.response.headers.get('Retry-After')
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        pass
            time.sleep(delay)

def enrich_task(description: str) -> TaskEnrichmentResponse:
    # Kill switch
    if os.environ.get("LLM_ENABLED", "1") == "0":
        return TaskEnrichmentResponse(
            category=CategoryEnum.other,
            urgency=UrgencyEnum.low,
            confidence=1.0,
            reason="AI disabled, returning fallback."
        )
        
    # Stub mode
    if os.environ.get("LLM_STUB", "0") == "1":
        return TaskEnrichmentResponse(
            category=CategoryEnum.work,
            urgency=UrgencyEnum.normal,
            confidence=0.9,
            reason="Stub mode enabled."
        )

    client = OpenAI(
        base_url=os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.environ.get("LLM_API_KEY", "dummy"),
        timeout=30.0,
        max_retries=0 # We do our own retries
    )
    
    model = os.environ.get("LLM_MODEL", "openrouter/free")
    system_prompt = load_prompt()
    
    # Wrap description in JSON to prevent injection
    safe_input = json.dumps({"description": description})
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": safe_input}
    ]
    
    try:
        raw_output = call_model_with_retry(client, model, messages, is_repair=False)
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI provider timed out")
    except APIStatusError as e:
        raise HTTPException(status_code=e.status_code, detail=f"AI provider error: {e.message}")
        
    # Stage 3: Validate and Repair
    try:
        clean_out = clean_json_response(raw_output)
        return TaskEnrichmentResponse.model_validate_json(clean_out)
    except (ValidationError, json.JSONDecodeError) as e:
        # Repair once
        repair_messages = messages + [
            {"role": "assistant", "content": raw_output},
            {"role": "user", "content": f"Your previous answer was rejected for this reason:\n{str(e)}\nReturn only corrected JSON matching the schema."}
        ]
        
        try:
            raw_output = call_model_with_retry(client, model, repair_messages, is_repair=True)
            clean_out = clean_json_response(raw_output)
            return TaskEnrichmentResponse.model_validate_json(clean_out)
        except Exception as e_repair:
            quarantine_logger.info(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "prompt_version": "v1",
                "input": description,
                "error": str(e_repair),
                "raw_output": raw_output
            }))
            raise HTTPException(status_code=422, detail="Failed to parse AI response into valid JSON after repair.")
