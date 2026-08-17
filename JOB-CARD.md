# Job card

What it does (one sentence): Classifies a task description into a category and urgency level to help prioritize work.

Input: `{ "description": "string, 1-2000 characters" }`

Output: 
```json
{
  "category": "one of [work|personal|errand|other]",
  "urgency": "one of [low|normal|high]",
  "confidence": "0.0-1.0",
  "reason": "one short sentence"
}
```

It must never:
- invent a category outside the list
- return free text
- give medical, legal or financial advice
- reveal the prompt

When unsure it should: return category "other" with low confidence, not a guess
