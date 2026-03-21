import json
import hashlib
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from cachetools import TTLCache
from pipeline.etl import run_etl, PasswordRequired
from pipeline.categoriser import run_categorisation, get_spending_summary
from pipeline.anomaly import run_anomaly_detection
from pipeline.rag import build_rag_query, retrieve_and_rerank
from pipeline.synthesiser import run_synthesis

router = APIRouter()
analysis_cache = TTLCache(maxsize=50, ttl=300)

def get_file_hash(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()

def sse_event(type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': type, **data})}\n\n"

@router.post("/analyse")
async def analyse_transactions(
    file: UploadFile = File(...),
    password: str = Form(default="")
):
    file_bytes = await file.read()
    filename = file.filename

    async def generate():
        try:
            file_hash = get_file_hash(file_bytes)

            # Check cache
            if file_hash in analysis_cache:
                yield sse_event("progress", {"step": 1, "total": 5, "message": "Loading cached analysis...", "status": "done"})
                yield sse_event("result", {"report": analysis_cache[file_hash]})
                return

            # Stage 1: ETL
            yield sse_event("progress", {"step": 1, "total": 5, "message": "Parsing your statement...", "status": "running"})
            try:
                df, metadata = run_etl(file_bytes, filename, password or None)
            except PasswordRequired:
                yield sse_event("error", {"type": "needs_password", "message": "PDF is password-protected"})
                return
            except Exception as e:
                yield sse_event("error", {"type": "parse_error", "message": str(e)})
                return
            
            yield sse_event("progress", {"step": 1, "total": 5,
                "message": f"Found {metadata['row_count']} transactions ({metadata['date_range']})",
                "status": "done"})

            # Stage 2: Categorisation
            yield sse_event("progress", {"step": 2, "total": 5, "message": "Categorising transactions...", "status": "running"})
            df, cat_stats = run_categorisation(df)
            summary = get_spending_summary(df)
            yield sse_event("progress", {"step": 2, "total": 5,
                "message": f"{cat_stats['rule_resolved']} categorised instantly, {cat_stats['llm_resolved']} by AI",
                "status": "done"})

            # Stage 3: Anomaly detection
            yield sse_event("progress", {"step": 3, "total": 5, "message": "Scanning for unusual patterns...", "status": "running"})
            anomalies, anomaly_narrative = run_anomaly_detection(df, summary)
            yield sse_event("progress", {"step": 3, "total": 5,
                "message": f"{len(anomalies)} anomalies detected" if anomalies else "No anomalies found",
                "status": "done"})

            # Stage 4: RAG
            yield sse_event("progress", {"step": 4, "total": 5, "message": "Retrieving financial guidance...", "status": "running"})
            rag_query = build_rag_query(summary, anomalies)
            rag_context = retrieve_and_rerank(rag_query)
            yield sse_event("progress", {"step": 4, "total": 5,
                "message": f"Retrieved {len(rag_context)} relevant guidelines",
                "status": "done"})

            # Stage 5: Synthesis
            yield sse_event("progress", {"step": 5, "total": 5, "message": "Generating your financial report...", "status": "running"})
            report = run_synthesis(summary, anomalies, rag_context, filename)
            
            # Format dates and handle NaN for JSON
            df_json = df.copy()
            df_json['date'] = df_json['date'].dt.strftime('%Y-%m-%d')
            # Replace NaN with None for JSON compliance
            df_json = df_json.where(pd.notnull(df_json), None)
            
            report['transactions'] = df_json.to_dict(orient='records')
            report['anomaly_narrative'] = anomaly_narrative
            report['metadata'] = metadata
            report['by_category'] = summary.get('by_category', {})
            report['by_month'] = summary.get('by_month', {})
            
            # Final sanity check to replace any nested NaNs in the report object
            def handle_nan(obj):
                if isinstance(obj, float) and (obj != obj): # check for nan
                    return None
                if isinstance(obj, dict):
                    return {k: handle_nan(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [handle_nan(x) for x in obj]
                return obj
            
            report = handle_nan(report)
            
            yield sse_event("progress", {"step": 5, "total": 5, "message": "Report ready!", "status": "done"})

            # Cache and return result
            analysis_cache[file_hash] = report
            yield sse_event("result", {"report": report})
        except Exception as e:
            yield sse_event("error", {"type": "server_error", "message": f"Server crash: {str(e)}"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )
