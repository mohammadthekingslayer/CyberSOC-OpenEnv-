"""
Inference script for CyberSOC OpenEnv - OpenEnv Competition Compliant.

MANDATORY ENVIRONMENT VARIABLES:
- API_KEY or HF_TOKEN: Your API key for the LLM provider
- API_BASE_URL: The API endpoint (default: Google Gemini)
- MODEL_NAME: The model identifier (default: gemini-2.0-flash-exp)

OUTPUT FORMAT:
- [START] task=<task_name> env=<benchmark> model=<model_name>
- [STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
- [END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""
import asyncio
import os
import sys
import json
import re
import textwrap
from typing import List, Optional

from openai import OpenAI
from dotenv import load_dotenv
from cyber_soc_env.models import SOCAction

load_dotenv()

# Environment variables with secure defaults
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL_NAME = os.getenv("MODEL_NAME") or "gemini-2.0-flash-exp"
BENCHMARK = os.getenv("CYBER_SOC_BENCHMARK", "cyber-soc-env")

# Execution parameters
MAX_STEPS = 8
SUCCESS_SCORE_THRESHOLD = 0.7  # 70% score required for PASS

SYSTEM_PROMPT = """You are an ELITE SOC (Security Operations Center) analyst with expertise in cybersecurity incident response.

Your mission is to investigate and respond to security threats efficiently and accurately.

AVAILABLE ACTIONS:
- analyze_log: Investigate a specific log entry, IP address, file hash, or domain
- block_ip: Block a malicious IP address at the firewall
- isolate_device: Quarantine an infected device by hostname
- mark_safe: Mark an entity as not a threat after investigation
- escalate: Escalate incident to senior security management
- run_scan: Execute malware scan on a workstation
- correlate_events: Connect multiple security events together

CRITICAL GUIDELINES:
1. ALWAYS analyze logs BEFORE taking destructive actions (block/isolate)
2. Be SPECIFIC with targets - extract exact IPs (e.g., '10.0.0.55'), hostnames (e.g., 'WS-042', 'DC-01'), or filenames (e.g., 'invoice.exe') directly from the ALERTS and LOGS. NEVER use generic targets like 'all', 'system', or 'logs'.
3. Follow proper incident response: Detect (analyze_log) → Contain (block_ip, isolate_device) → Eradicate → Recover (mark_safe).
4. Do NOT repeat actions you have already taken. Review the 'ACTIONS ALREADY TAKEN' list.
5. Once you have contained the primary threats (blocked IPs, isolated hosts), you MUST use 'mark_safe' on the affected system to finalize recovery and end the episode.

RESPONSE FORMAT:
Respond ONLY with a valid JSON object:
{
  "action_type": "<action_type>",
  "target": "<specific_target>"
}

Do NOT include reasoning or markdown. Output minimal JSON for maximum speed.

No markdown, no extra text, just JSON."""

def log_start(task: str, env: str, model: str) -> None:
    """Log episode start in required format."""
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log each step in required format."""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float], kpis: dict = None) -> None:
    """Log episode end in required format."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_val = str(success).lower()
    kpis_json = json.dumps(kpis) if kpis else "{}"
    print(f"[END] success={success_val} steps={steps} score={score:.3f} rewards={rewards_str} kpis={kpis_json}", flush=True)

def build_user_prompt(obs_dict: dict, step: int, action_history: List[str]) -> str:
    """Build context-rich user prompt from observation."""
    logs = obs_dict.get("logs", [])
    alerts = obs_dict.get("alerts", [])
    threat_level = obs_dict.get("threat_level", "unknown").upper()
    message = obs_dict.get("message", "")
    
    # Format recent logs (last 5)
    recent_logs = logs[-5:] if logs else []
    logs_display = "\n".join(recent_logs) if recent_logs else "No new logs"
    
    # Format active alerts
    alerts_display = "\n".join(alerts) if alerts else "No active alerts"
    
    # Format action history
    history_display = "\n".join(action_history) if action_history else "None"
    
    return f"""=== SOC INCIDENT DASHBOARD (Step {step}) ===

THREAT LEVEL: {threat_level}
LATEST UPDATE: {message}

ACTIONS ALREADY TAKEN:
{history_display}

RECENT LOGS:
{logs_display}

ACTIVE ALERTS:
{alerts_display}

Your task: Investigate and respond appropriately. Extract specific targets from the logs/alerts. Do not repeat past actions. Return your action as JSON.""".strip()

async def get_action_from_llm(client: OpenAI, obs_dict: dict, step: int, action_history: List[str]) -> SOCAction:
    """Query LLM for next action with robust error handling."""
    import time
    import random
    
    user_prompt = build_user_prompt(obs_dict, step, action_history)
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep((2 ** attempt) + random.uniform(0.1, 1))

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=50,
                timeout=15,
            )
            text = (response.choices[0].message.content or "").strip()
            
            # Robust JSON extraction
            try:
                # Try parsing directly first
                data = json.loads(text)
            except json.JSONDecodeError:
                # Look for JSON structure in text
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                else:
                    raise

            return SOCAction(
                action_type=str(data.get("action_type", "analyze_log")),
                target=str(data.get("target", "all")),
                reasoning="Fast execution",
            )
            
        except (json.JSONDecodeError, ValueError) as e:
            if attempt == max_retries - 1:
                return SOCAction(action_type="analyze_log", target="all", reasoning=f"Parse Error: {str(e)}")
        except Exception as e:
            err_msg = str(e).lower()
            if "authentication" in err_msg or "api key" in err_msg or "401" in err_msg or "403" in err_msg:
                print(f"[ERROR] API Authentication failed: {e}", flush=True)
                sys.exit(1)
            if any(x in err_msg for x in ["429", "rate", "quota", "limit", "timeout"]):
                time.sleep((2 ** attempt) * 15 + random.uniform(0, 5))
                continue
            if attempt == max_retries - 1:
                return SOCAction(action_type="analyze_log", target="all", reasoning=f"API Error: {str(e)}")
    
    # Final fallback
    return SOCAction(
        action_type="analyze_log",
        target="all",
        reasoning="Max retries exceeded"
    )

async def run_task(client: OpenAI, task_name: str):
    """Run a single task episode and log results."""
    from cyber_soc_env.env.environment import SOCEnvironment
    from dataclasses import asdict
    
    env = SOCEnvironment(task_id=task_name)
    
    rewards: List[float] = []
    action_history: List[str] = []
    steps_taken = 0
    total_latency_sec = 0.0
    success = False
    
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    
    try:
        # Reset environment
        obs = env.reset()
        obs_dict = asdict(obs)
        
        # Episode loop
        for step in range(1, MAX_STEPS + 1):
            if env.is_done:
                break
            
            # Get action from LLM
            start_time = time.perf_counter()
            action = await get_action_from_llm(client, obs_dict, step, action_history)
            end_time = time.perf_counter()
            total_latency_sec += (end_time - start_time)
            # Handle both string and enum action_type
            action_type_str = action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type)
            action_str = f"{action_type_str}(target='{action.target}')"
            action_history.append(action_str)
            
            # Extract error if it's our fallback
            error_msg = action.reasoning if action.reasoning.startswith(("API Error", "Parse Error")) else None
            
            # Execute action
            obs_new = env.step(action)
            obs_dict = asdict(obs_new)
            
            reward = obs_new.reward
            done = obs_new.done
            
            rewards.append(reward)
            steps_taken = step
            
            log_step(step=step, action=action_str, reward=reward, done=done, error=error_msg)
            
            if done:
                break
        
        # Grade episode (score in range 0.0 - 1.0)
        grade_result = env.grade_episode(task_id=task_name)
        score = grade_result.score
        kpis = grade_result.kpis
        
        avg_latency_ms = (total_latency_sec / max(1, steps_taken)) * 1000
        kpis["avg_latency_ms"] = round(avg_latency_ms, 2)
        
        success = score >= SUCCESS_SCORE_THRESHOLD
        
    except Exception as e:
        print(f"[DEBUG] Episode error: {e}", file=sys.stderr)
        score = 0.0
        kpis = {}
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards, kpis=kpis)

async def main():
    """Main inference entry point - runs all 3 tasks sequentially."""
    if not API_KEY:
        print("[ERROR] No API key found. Set API_KEY or HF_TOKEN environment variable.", file=sys.stderr)
        sys.exit(1)
    
    # Initialize OpenAI client
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    # Run all 3 tasks in order
    for task_name in ["task1", "task2", "task3"]:
        await run_task(client, task_name)

if __name__ == "__main__":
    asyncio.run(main())
