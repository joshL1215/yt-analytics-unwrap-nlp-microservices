from typing import List, Tuple
import numpy as np

def prune_comments(comments: List[str], min_length: int = 20) -> List[str]:
    kept_comments = []

    # Take simple random sample
    sample_size = min(500, len(comments))
    comments = np.random.choice(comments, size=sample_size, replace=False)

    # Length pruning
    for comment in comments:
        if len(comment.strip()) >= min_length:
            kept_comments.append(comment)

    return kept_comments