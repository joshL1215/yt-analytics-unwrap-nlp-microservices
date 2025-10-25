from app.services.prune import prune_comments
from app.services.comment_inference import analyze_comments

async def comment_analysis_handler(payload: dict) -> dict:

    comments = payload.get("comments", [])
    min_length = payload.get("min_length", 10)
    product_context = payload.get("product_context")  # Optional context about the video/product
    batch_size = payload.get("batch_size", 20)  # Number of comments per LLM call

    # Step 1: Prune comments and simple random sample
    kept_comments = prune_comments(comments, min_length)

    # Step 2: Analyze kept comments with LLM
    analysis_results = await analyze_comments(
        kept_comments,
        product_context=product_context,
        batch_size=batch_size
    )

    res = {
        "analyses": analysis_results["analyses"],
        "analysis_stats": analysis_results["stats"],
        "pruning_info": {
            "kept_comments": kept_comments,
            "all_comments"
            "stats": {
                "total": len(comments),
                "kept": len(kept_comments),
            }
        }
    }

    return res

def video_analysis_handler(payload: dict):
    # TODO: Implement video analysis
    return {}
