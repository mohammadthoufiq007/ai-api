import os
import sys
# Add parent directory to path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from src.llm.client import enrich_task

def run_evals():
    with open("evals/cases.json", "r") as f:
        cases = json.load(f)
        
    correct = 0
    total = len(cases)
    failed_cases = []
    
    print(f"Running {total} eval cases...")
    
    for idx, case in enumerate(cases):
        print(f"Case {idx+1}/{total}: {case['description']}")
        try:
            res = enrich_task(case['description'])
            match = True
            
            if res.category.value != case['expected_category']:
                match = False
                print(f"  [FAIL] Category mismatch. Expected {case['expected_category']}, got {res.category.value}")
                
            if res.urgency.value != case['expected_urgency']:
                match = False
                print(f"  [FAIL] Urgency mismatch. Expected {case['expected_urgency']}, got {res.urgency.value}")
                
            if match:
                print("  [PASS] Pass")
                correct += 1
            else:
                failed_cases.append(case)
                
        except Exception as e:
            print(f"  [FAIL] Exception: {str(e)}")
            failed_cases.append(case)
            
    score = (correct / total) * 100
    print(f"\nFinal Score: {correct}/{total} ({score:.1f}%)")
    
    if failed_cases:
        print("\nFailed Cases:")
        for fc in failed_cases:
            print(f" - {fc['description']}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_evals()
