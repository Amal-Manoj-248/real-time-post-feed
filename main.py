from flask import Flask, request, jsonify
import json
import random
import time
from uuid import uuid4
from typing import List
from collections import defaultdict
from bisect import bisect_left, bisect_right
from functools import lru_cache

app = Flask(__name__)

# Data storage
posts = []
inverted_index = defaultdict(list)
timestamp_index = []

# Post model
class PostModel:
    def __init__(self, timestamp: int, tags: List[str], content: str):
        self.id = str(uuid4())
        self.timestamp = timestamp
        self.tags = tags
        self.content = content

# Add a new post
def add_post(post: PostModel):
    posts.append(post)
    timestamp_index.append((post.timestamp, post.id))
    timestamp_index.sort()
    for tag in post.tags:
        inverted_index[tag].append(post.id)
    return {"message": "Post added successfully.", "post_id": post.id}

# Caching function for frequently queried posts
@lru_cache(maxsize=128)
def cached_get_posts(tags: tuple = None, start_time: int = None, end_time: int = None, k: int = 10):
    return get_posts(tags=list(tags) if tags else None, start_time=start_time, end_time=end_time, k=k)

# Get posts based on filters
def get_posts(tags: List[str] = None, start_time: int = None, end_time: int = None, k: int = 10):
    if start_time and end_time and start_time > end_time:
        raise ValueError("start_time cannot be greater than end_time.")

    # Filter by time range
    start_idx = bisect_left(timestamp_index, (start_time or 0, ""))
    end_idx = bisect_right(timestamp_index, (end_time or float("inf"), ""))
    time_filtered_posts = {post_id for _, post_id in timestamp_index[start_idx:end_idx]}

    # Filter by tags
    if tags:
        tag_filtered_posts = {post_id for tag in tags for post_id in inverted_index.get(tag, [])}
        filtered_post_ids = time_filtered_posts.intersection(tag_filtered_posts)
    else:
        filtered_post_ids = time_filtered_posts

    # Retrieve and sort posts
    filtered_posts = [post for post in posts if post.id in filtered_post_ids]
    filtered_posts.sort(key=lambda p: p.timestamp, reverse=True)

    result = [
        {"id": post.id, "timestamp": post.timestamp, "tags": post.tags, "content": post.content}
        for post in filtered_posts[:k]
    ]
    return {"posts": result, "total_count": len(filtered_post_ids)}

# Predefined tags and content
TAGS = ["sports", "technology", "news", "entertainment", "science", "health", "education"]
CONTENT = [
    "This is an amazing post about sports.",
    "Learn about the latest in technology.",
    "Breaking news happening right now.",
    "Check out this new movie review.",
    "Discover the mysteries of science.",
    "Health tips to improve your lifestyle.",
    "Education trends to watch for in 2024."
]

# Generate random posts
def generate_post():
    timestamp = int(time.time()) - random.randint(0, 60 * 60 * 24 * 365)
    tags = random.sample(TAGS, random.randint(1, 3))
    content = random.choice(CONTENT)
    return PostModel(timestamp=timestamp, tags=tags, content=content)

# Populate with test posts
def send_posts(num_posts: int):
    for _ in range(num_posts):
        add_post(generate_post())

# API Routes
@app.route('/get_posts', methods=['GET'])
def api_get_posts():
    try:
        tags = request.args.get('tags')
        start_time = request.args.get('start_time', type=int)
        end_time = request.args.get('end_time', type=int)
        k = request.args.get('k', 10, type=int)
        tags = json.loads(tags) if tags else None

        result = get_posts(tags=tags, start_time=start_time, end_time=end_time, k=k)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/add_post', methods=['POST'])
def api_add_post():
    try:
        data = request.get_json()
        timestamp = data['timestamp']
        tags = data['tags']
        content = data['content']
        post = PostModel(timestamp=timestamp, tags=tags, content=content)
        result = add_post(post)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Debugging and initialization
if __name__ == "__main__":
    print("Initializing backend...")
    send_posts(10000)  # Generate 10,000 random posts for testing
    print("Backend initialized with 10,000 test posts.")
    app.run(host="0.0.0.0", port=5000)
