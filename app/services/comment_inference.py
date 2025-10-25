from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum

from app.util.unwrap_openai import create_openai_completion, GPT5Deployment, ReasoningEffort


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class CommentAnalysisResult(BaseModel):
    """Structured analysis result for a single comment."""

    comment_index: int = Field(..., description="The index of the comment in the batch (0-indexed)")
    product_sentiment: SentimentType = Field(..., description="Sentiment specifically about the product, not just general sentiment")
    has_issue: bool = Field(..., description="Whether this comment mentions a specific issue with the product")
    issue_description: Optional[str] = Field(None, description="Brief description of the issue if has_issue is True, max 50 chars")
    topic: str = Field(..., description="General topic/category of the comment as it relates to the product, max 30 chars")


class BatchAnalysisResult(BaseModel):
    """Analysis results for a batch of comments."""

    analyses: List[CommentAnalysisResult] = Field(..., description="List of individual comment analyses")


async def analyze_comments_batch(
    comments: List[str],
    product_context: Optional[str] = None,
    batch_size: int = 20
) -> List[Dict]:
    """
    Analyze a batch of comments using Azure OpenAI with structured output.

    Args:
        comments: List of comment strings to analyze
        product_context: Optional context about what product/video these comments are for
        batch_size: Number of comments to process in each LLM call (default 20)

    Returns:
        List of analysis dictionaries containing sentiment, issues, and topics
    """
    all_results = []

    # Process comments in batches
    for i in range(0, len(comments), batch_size):
        batch = comments[i:i+batch_size]
        batch_results = await _analyze_single_batch(batch, i, product_context)
        all_results.extend(batch_results)

    return all_results


async def _analyze_single_batch(
    batch: List[str],
    start_index: int,
    product_context: Optional[str] = None
) -> List[Dict]:
    """Analyze a single batch of comments with structured output."""

    # Format comments with indices
    formatted_comments = "\n".join([
        f"[{idx}] {comment}"
        for idx, comment in enumerate(batch)
    ])

    context_note = f"Product/Video Context: {product_context}\n\n" if product_context else ""

    # Create system and user messages
    messages = [
        {
            "role": "system",
            "content": """You are an expert at analyzing YouTube comments about products/videos.
Your task is to extract structured information from each comment:

1. PRODUCT SENTIMENT: Focus specifically on how the commenter feels about the PRODUCT/VIDEO itself, not their general mood. Look for opinions about features, quality, usefulness, etc.

2. ISSUE IDENTIFICATION: Only mark has_issue=True if the comment explicitly mentions a problem, bug, complaint, or negative experience with the product. Be specific in describing the issue.

3. TOPIC CATEGORIZATION: Identify the main topic/theme of the comment as it relates to the product. Examples: "feature request", "bug report", "pricing", "performance", "UI/UX", "comparison", "tutorial request", "general praise", etc.

Keep outputs concise and deterministic. Be precise and consistent in categorization."""
        },
        {
            "role": "user",
            "content": f"""{context_note}Analyze the following {len(batch)} comments. Return structured analysis for each:

{formatted_comments}"""
        }
    ]

    # Call OpenAI with forced structured output
    response = await create_openai_completion(
        messages=messages,
        model=GPT5Deployment.GPT_5_NANO,
        reasoning_effort=ReasoningEffort.MINIMAL,
        tools=[BatchAnalysisResult],
        tool_choice="required",
        max_completion_tokens=4096
    )

    # Parse tool call response
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        import json
        result_data = json.loads(tool_call.function.arguments)
        batch_result = BatchAnalysisResult(**result_data)

        # Convert to list of dicts with absolute indices
        return [
            {
                "comment": batch[analysis.comment_index],
                "original_index": start_index + analysis.comment_index,
                "product_sentiment": analysis.product_sentiment,
                "has_issue": analysis.has_issue,
                "issue_description": analysis.issue_description,
                "topic": analysis.topic
            }
            for analysis in batch_result.analyses
        ]

    return []


async def analyze_comments(
    comments: List[str],
    product_context: Optional[str] = None,
    batch_size: int = 20
) -> Dict:
    """
    Main function to analyze comments with batching support.

    Returns a dictionary with:
    - analyses: List of individual comment analyses
    - stats: Aggregated statistics about sentiments, issues, topics
    """
    analyses = await analyze_comments_batch(comments, product_context, batch_size)

    # Compute aggregate stats
    stats = {
        "total_analyzed": len(analyses),
        "sentiment_breakdown": {
            "positive": sum(1 for a in analyses if a["product_sentiment"] == "positive"),
            "negative": sum(1 for a in analyses if a["product_sentiment"] == "negative"),
            "neutral": sum(1 for a in analyses if a["product_sentiment"] == "neutral"),
            "mixed": sum(1 for a in analyses if a["product_sentiment"] == "mixed"),
        },
        "issues_found": sum(1 for a in analyses if a["has_issue"]),
        "unique_topics": len(set(a["topic"] for a in analyses))
    }

    return {
        "analyses": analyses,
        "stats": stats
    }
