from __future__ import annotations
import time
import re

from telemetry.logger import logger
from telemetry.cost import cost_from_usage
from telemetry.redact import redact_value

def mitigate(call_next, question, config, context):
    import traceback
    try:
        t0 = time.time()
        result = call_next(question, config)
        meta = result.get("meta", {})
        usage = meta.get("usage", {})
        
        answer = result.get("answer")
        if answer:
            result["answer"] = redact_value(answer)
            
        trace = result.get("trace", [])
        actions = [step.get("action") for step in trace if isinstance(step, dict) and "action" in step]
        
        logger.log_event("CALL", {
            "qid": context.get("qid"),
            "session": context.get("session_id"),
            "turn": context.get("turn_index"),
            "wall_ms": int((time.time() - t0) * 1000),
            "latency_ms": meta.get("latency_ms"),
            "usage": usage,
            "cost_usd": cost_from_usage(meta.get("model", ""), usage),
            "tools": meta.get("tools_used", []),
            "status": result.get("status"),
            "steps": result.get("steps"),
            "actions": actions
        })
        return result
    except Exception as e:
        return {"answer": f"WRAPPER CRASH: {e}\n{traceback.format_exc()}", "status": "wrapper_error", "steps": 0, "trace": []}
