from typing import List
from .models import BenchmarkCase, BenchmarkAnswer, ExpectedScores


def get_benchmark_dataset() -> List[BenchmarkCase]:
    """Returns a curated dataset of realistic interview benchmark cases with ground-truth expected scores.
    
    Covers 7 distinct domain areas:
    - Python
    - Data Structures
    - SQL
    - Machine Learning
    - System Design
    - Behavioral
    - Problem Solving
    """
    cases = [
        # 1. Python
        BenchmarkCase(
            case_id="case_01_python",
            question="What are Python decorators, how do they work under the hood, and what are common use cases for them?",
            topic="Python",
            estimated_difficulty="Medium",
            expected_topics=["Higher-order functions", "Closures", "functools.wraps", "Syntax sugar", "Cross-cutting concerns"],
            evaluation_rubric=(
                "Excellent (90): Explains functions as first-class objects, closures, @functools.wraps, syntax sugar (@), and gives clear practical examples.\n"
                "Good (75): Explains wrapper functions and syntax sugar with a practical example, misses @wraps or closure details.\n"
                "Average (60): Mentions modifying functions, basic syntax, but vague on how it works under the hood.\n"
                "Weak (40): Confuses decorators with annotations/classes or provides incorrect wrapper syntax.\n"
                "Incorrect (15): Claims decorators are used for decorating text or UI elements."
            ),
            answers=[
                BenchmarkAnswer(
                    quality_level="excellent",
                    candidate_answer=(
                        "In Python, decorators are higher-order functions that take a function as an argument and return a new function, "
                        "allowing you to extend or modify behavior without changing the original code. Under the hood, Python treats functions "
                        "as first-class objects. A decorator leverages closures to preserve outer scope variables. Using `@decorator_name` is syntax sugar "
                        "for `func = decorator_name(func)`. It is best practice to use `@functools.wraps(func)` on the inner function to preserve docstrings "
                        "and function metadata. Common use cases include logging, authentication, execution timing, and caching (like `@lru_cache`)."
                    ),
                    expected_scores=ExpectedScores(technical_score=90.0, communication_score=90.0, reasoning_score=90.0, confidence_score=90.0, overall_score=90.0)
                ),
                BenchmarkAnswer(
                    quality_level="good",
                    candidate_answer=(
                        "A decorator in Python is a function that wraps another function to add behavior before or after execution. "
                        "The `@` symbol is syntactic sugar. You write a function that defines a nested wrapper function and returns it. "
                        "For example, you can write a timing decorator that records start time, calls the function, records end time, and prints duration. "
                        "They are heavily used in frameworks like Flask for route handlers and authentication checks."
                    ),
                    expected_scores=ExpectedScores(technical_score=75.0, communication_score=80.0, reasoning_score=75.0, confidence_score=75.0, overall_score=75.0)
                ),
                BenchmarkAnswer(
                    quality_level="average",
                    candidate_answer=(
                        "Decorators are used in Python to modify the behavior of functions. You put `@decorator` above a function definition. "
                        "It runs extra code when the function is called. For example, checking if a user is logged in before running a function."
                    ),
                    expected_scores=ExpectedScores(technical_score=60.0, communication_score=65.0, reasoning_score=60.0, confidence_score=60.0, overall_score=60.0)
                ),
                BenchmarkAnswer(
                    quality_level="weak",
                    candidate_answer=(
                        "Decorators are like class annotations in Java. You use `@` symbol to declare variables or make functions private in Python. "
                        "I haven't built custom ones myself but I've seen them used."
                    ),
                    expected_scores=ExpectedScores(technical_score=40.0, communication_score=50.0, reasoning_score=35.0, confidence_score=40.0, overall_score=40.0)
                ),
                BenchmarkAnswer(
                    quality_level="incorrect",
                    candidate_answer=(
                        "Python decorators are design tools in CSS and HTML used to format terminal text with colors and underline output styles."
                    ),
                    expected_scores=ExpectedScores(technical_score=15.0, communication_score=30.0, reasoning_score=10.0, confidence_score=20.0, overall_score=15.0)
                )
            ]
        ),

        # 2. Data Structures
        BenchmarkCase(
            case_id="case_02_data_structures",
            question="How does a Hash Table achieve average O(1) time complexity for search, and how are collisions handled?",
            topic="Data Structures",
            estimated_difficulty="Medium",
            expected_topics=["Hash function", "Array indexing", "Collision resolution", "Chaining", "Open addressing", "Load factor"],
            evaluation_rubric=(
                "Excellent (90): Explains hash function mapping key to index, array access, chaining (linked list/tree) vs open addressing (linear/quadratic probing), and load factor / rehashing.\n"
                "Good (75): Explains hashing to index and details chaining or probing well, mentions load factor.\n"
                "Average (60): Explains keys map to indices, mentions collisions happen when keys hash to same index, gives basic chaining explanation.\n"
                "Weak (40): States hash tables are fast key-value pairs but cannot explain hash functions or collision resolution.\n"
                "Incorrect (15): Claims hash tables sort keys in binary search tree order to get O(1)."
            ),
            answers=[
                BenchmarkAnswer(
                    quality_level="excellent",
                    candidate_answer=(
                        "A Hash Table maps keys to bucket indices in an array using a hash function. Computing `index = hash(key) % array_capacity` "
                        "takes O(1) time, allowing constant-time array access. Collisions occur when different keys hash to the same index. "
                        "Common collision resolution techniques are: 1) Chaining, where each bucket holds a linked list or self-balancing tree of entries. "
                        "2) Open Addressing (e.g. Linear Probing, Double Hashing), where collision causes a probe for the next open slot. "
                        "To maintain average O(1) performance, when the load factor (N/capacity) exceeds a threshold (e.g., 0.75), the table rehashes into a larger array."
                    ),
                    expected_scores=ExpectedScores(technical_score=90.0, communication_score=90.0, reasoning_score=90.0, confidence_score=90.0, overall_score=90.0)
                ),
                BenchmarkAnswer(
                    quality_level="good",
                    candidate_answer=(
                        "Hash tables convert keys into integer indices using a hash function. Since accessing an array element by index is O(1), "
                        "looking up a key is O(1) on average. When two keys yield the same index (a collision), chaining is commonly used: "
                        "the bucket stores a list of key-value pairs, and you search that list. If the table gets too full, performance degrades, so it resizes."
                    ),
                    expected_scores=ExpectedScores(technical_score=75.0, communication_score=80.0, reasoning_score=75.0, confidence_score=75.0, overall_score=75.0)
                ),
                BenchmarkAnswer(
                    quality_level="average",
                    candidate_answer=(
                        "A hash table uses a hash function to compute a location for each key. It's O(1) because it directly jumps to the index. "
                        "If two items hash to the same place, a collision happens, and you can store both in a list at that index."
                    ),
                    expected_scores=ExpectedScores(technical_score=60.0, communication_score=65.0, reasoning_score=60.0, confidence_score=60.0, overall_score=60.0)
                ),
                BenchmarkAnswer(
                    quality_level="weak",
                    candidate_answer=(
                        "Hash tables store key-value pairs like dictionaries. Search is O(1) because Python handles it fast in memory. "
                        "I don't know much about collisions."
                    ),
                    expected_scores=ExpectedScores(technical_score=40.0, communication_score=45.0, reasoning_score=35.0, confidence_score=40.0, overall_score=40.0)
                ),
                BenchmarkAnswer(
                    quality_level="incorrect",
                    candidate_answer=(
                        "Hash tables maintain keys in a binary search tree. Every time you search, it performs binary search on the array which is O(1)."
                    ),
                    expected_scores=ExpectedScores(technical_score=15.0, communication_score=30.0, reasoning_score=10.0, confidence_score=20.0, overall_score=15.0)
                )
            ]
        ),

        # 3. SQL
        BenchmarkCase(
            case_id="case_03_sql",
            question="What is the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN, and when would you use an index on a database column?",
            topic="SQL",
            estimated_difficulty="Medium",
            expected_topics=["INNER JOIN", "LEFT JOIN", "FULL OUTER JOIN", "B-Tree index", "WHERE clause", "Write overhead"],
            evaluation_rubric=(
                "Excellent (90): Clearly defines set operations for all 3 joins, explains B-tree indexing mechanism, WHERE/JOIN performance boosts, and write overhead trade-offs.\n"
                "Good (75): Accurately differentiates the 3 joins and explains indexing based on frequent lookup columns and write trade-offs.\n"
                "Average (60): Differentiates INNER vs LEFT join clearly, vague on FULL OUTER join and indexing mechanics.\n"
                "Weak (40): Confuses LEFT and RIGHT joins, vague explanation of database indexes.\n"
                "Incorrect (15): Claims INNER JOIN returns all rows from both tables and indexes decrease performance."
            ),
            answers=[
                BenchmarkAnswer(
                    quality_level="excellent",
                    candidate_answer=(
                        "INNER JOIN returns only rows that have matching values in both tables. LEFT JOIN returns all rows from the left table and "
                        "matching rows from the right table, with NULLs for non-matching right rows. FULL OUTER JOIN returns all rows from both tables, "
                        "filling NULLs wherever matching records don't exist. You add a database index (typically B-Tree) on columns frequently used in "
                        "WHERE clauses, JOIN conditions, or ORDER BY statements to turn full table scans O(N) into B-Tree lookups O(log N). "
                        "However, indexes add write overhead on INSERT/UPDATE/DELETE operations, so they should be used judiciously."
                    ),
                    expected_scores=ExpectedScores(technical_score=90.0, communication_score=90.0, reasoning_score=90.0, confidence_score=90.0, overall_score=90.0)
                ),
                BenchmarkAnswer(
                    quality_level="good",
                    candidate_answer=(
                        "INNER JOIN only includes rows where the join condition matches in both tables. LEFT JOIN keeps all rows from the first table "
                        "and brings matching rows from the second table. FULL OUTER JOIN keeps everything from both tables. "
                        "Indexes speed up SELECT queries on columns that are filtered or joined often, but you shouldn't index every column because it slows down writes."
                    ),
                    expected_scores=ExpectedScores(technical_score=75.0, communication_score=80.0, reasoning_score=75.0, confidence_score=75.0, overall_score=75.0)
                ),
                BenchmarkAnswer(
                    quality_level="average",
                    candidate_answer=(
                        "INNER JOIN gives matching data from both tables. LEFT JOIN gives all rows from left table. FULL OUTER JOIN merges everything. "
                        "Indexes are added to columns to make queries run faster when searching for data."
                    ),
                    expected_scores=ExpectedScores(technical_score=60.0, communication_score=60.0, reasoning_score=60.0, confidence_score=60.0, overall_score=60.0)
                ),
                BenchmarkAnswer(
                    quality_level="weak",
                    candidate_answer=(
                        "INNER JOIN combines tables. LEFT JOIN is the same as RIGHT JOIN. Indexes are used when you have primary keys."
                    ),
                    expected_scores=ExpectedScores(technical_score=40.0, communication_score=40.0, reasoning_score=35.0, confidence_score=40.0, overall_score=40.0)
                ),
                BenchmarkAnswer(
                    quality_level="incorrect",
                    candidate_answer=(
                        "INNER JOIN takes all rows from both tables even if they don't match. Indexes slow down queries and should never be used."
                    ),
                    expected_scores=ExpectedScores(technical_score=15.0, communication_score=25.0, reasoning_score=10.0, confidence_score=20.0, overall_score=15.0)
                )
            ]
        ),

        # 4. Machine Learning
        BenchmarkCase(
            case_id="case_04_machine_learning",
            question="What is the bias-variance tradeoff in Machine Learning, and how do overfitting and underfitting relate to it?",
            topic="Machine Learning",
            estimated_difficulty="Medium",
            expected_topics=["Bias", "Variance", "Overfitting", "Underfitting", "Model complexity", "Regularization"],
            evaluation_rubric=(
                "Excellent (90): Defines bias (erroneous assumptions / underfitting) and variance (sensitivity to noise / overfitting), total error decomposition, and resolution strategies (regularization, data, model capacity).\n"
                "Good (75): Accurately defines bias and variance, connects to under/overfitting, mentions model complexity.\n"
                "Average (60): Connects bias to underfitting and variance to overfitting, but explanations are superficial.\n"
                "Weak (40): Confuses bias with human prejudice or gives inverted definitions.\n"
                "Incorrect (15): Claims high variance means high accuracy."
            ),
            answers=[
                BenchmarkAnswer(
                    quality_level="excellent",
                    candidate_answer=(
                        "The bias-variance tradeoff describes the goal of minimizing two sources of error in predictive models. "
                        "Bias is error from overly simplistic assumptions; high bias leads to underfitting where the model fails to capture underlying patterns. "
                        "Variance is error from sensitivity to small fluctuations in the training data; high variance leads to overfitting where the model learns noise. "
                        "Total expected error = Bias^2 + Variance + Irreducible Error. As model complexity increases, bias decreases but variance increases. "
                        "Optimal generalization is achieved at the sweet spot using techniques like cross-validation, L1/L2 regularization, and ensemble methods."
                    ),
                    expected_scores=ExpectedScores(technical_score=90.0, communication_score=90.0, reasoning_score=90.0, confidence_score=90.0, overall_score=90.0)
                ),
                BenchmarkAnswer(
                    quality_level="good",
                    candidate_answer=(
                        "Bias is the error introduced by approximating a real-world problem with a simple model, leading to underfitting. "
                        "Variance is how much the predictions change for different training sets; high variance causes overfitting because the model memorizes the training data. "
                        "The tradeoff means you want a model complex enough to avoid underfitting, but constrained enough (e.g. through regularization) to avoid overfitting."
                    ),
                    expected_scores=ExpectedScores(technical_score=75.0, communication_score=80.0, reasoning_score=75.0, confidence_score=75.0, overall_score=75.0)
                ),
                BenchmarkAnswer(
                    quality_level="average",
                    candidate_answer=(
                        "High bias means underfitting because the model is too simple. High variance means overfitting because the model is too complex. "
                        "You need to balance them so your model generalizes well on test data."
                    ),
                    expected_scores=ExpectedScores(technical_score=60.0, communication_score=60.0, reasoning_score=60.0, confidence_score=60.0, overall_score=60.0)
                ),
                BenchmarkAnswer(
                    quality_level="weak",
                    candidate_answer=(
                        "Bias is statistical bias in the dataset when data is unfair. Variance is how much the dataset varies. You want low bias and low variance."
                    ),
                    expected_scores=ExpectedScores(technical_score=40.0, communication_score=40.0, reasoning_score=30.0, confidence_score=40.0, overall_score=40.0)
                ),
                BenchmarkAnswer(
                    quality_level="incorrect",
                    candidate_answer=(
                        "High variance means the model is 100% accurate and has no errors. Bias means the model is calibrated properly."
                    ),
                    expected_scores=ExpectedScores(technical_score=15.0, communication_score=25.0, reasoning_score=10.0, confidence_score=20.0, overall_score=15.0)
                )
            ]
        ),

        # 5. System Design
        BenchmarkCase(
            case_id="case_05_system_design",
            question="How would you design a rate limiter service to protect an API from DDoS attacks or excessive requests?",
            topic="System Design",
            estimated_difficulty="Hard",
            expected_topics=["Token Bucket / Sliding Window", "Distributed cache (Redis)", "HTTP 429", "API Gateway", "Scalability"],
            evaluation_rubric=(
                "Excellent (90): Details algorithm choice (Token Bucket / Sliding Window Log), centralized memory store (Redis with Lua script), HTTP 429 status code response, and API Gateway placement.\n"
                "Good (75): Explains algorithm (fixed/sliding window) and Redis-backed storage, handles HTTP 429.\n"
                "Average (60): Mentions counting requests per IP/user in Redis and blocking requests over the limit.\n"
                "Weak (40): Suggests blocking IP addresses manually or storing request counts in local server memory.\n"
                "Incorrect (15): Suggests adding more servers to handle infinite traffic without limiting."
            ),
            answers=[
                BenchmarkAnswer(
                    quality_level="excellent",
                    candidate_answer=(
                        "I would deploy a rate limiter at the API Gateway level using the Token Bucket or Sliding Window Counter algorithm. "
                        "For a distributed setup, state is stored in a Redis cluster using Lua scripts to ensure atomic increment and check operations. "
                        "Key identification can be based on User ID, API Key, or Client IP. When requests exceed the defined limit (e.g. 100 req/min), "
                        "the rate limiter immediately returns HTTP 429 Too Many Requests with headers like `X-RateLimit-Retry-After`. "
                        "Redis key expiration (TTL) handles automatic window resetting."
                    ),
                    expected_scores=ExpectedScores(technical_score=90.0, communication_score=90.0, reasoning_score=90.0, confidence_score=90.0, overall_score=90.0)
                ),
                BenchmarkAnswer(
                    quality_level="good",
                    candidate_answer=(
                        "I would use a Sliding Window algorithm implemented in Redis. When a request comes in, we check the request count for that user ID "
                        "in the current minute window. If count < max, we increment and allow the request. If count >= max, we reject it with HTTP 429. "
                        "Using Redis ensures that multiple app servers share the same rate limit counters."
                    ),
                    expected_scores=ExpectedScores(technical_score=75.0, communication_score=80.0, reasoning_score=75.0, confidence_score=75.0, overall_score=75.0)
                ),
                BenchmarkAnswer(
                    quality_level="average",
                    candidate_answer=(
                        "I would keep a counter for each user IP in a Redis cache. Every request increments the counter. "
                        "If the counter exceeds 100 in a minute, return an error message to the client until the minute resets."
                    ),
                    expected_scores=ExpectedScores(technical_score=60.0, communication_score=65.0, reasoning_score=60.0, confidence_score=60.0, overall_score=60.0)
                ),
                BenchmarkAnswer(
                    quality_level="weak",
                    candidate_answer=(
                        "You can write an if statement in python code with a global variable counter. Increment counter on request, if counter > 10, return error."
                    ),
                    expected_scores=ExpectedScores(technical_score=40.0, communication_score=45.0, reasoning_score=35.0, confidence_score=40.0, overall_score=40.0)
                ),
                BenchmarkAnswer(
                    quality_level="incorrect",
                    candidate_answer=(
                        "To stop DDoS attacks you don't limit requests, you just buy infinite RAM and CPU on AWS so the server never crashes."
                    ),
                    expected_scores=ExpectedScores(technical_score=15.0, communication_score=20.0, reasoning_score=10.0, confidence_score=20.0, overall_score=15.0)
                )
            ]
        ),

        # 6. Behavioral
        BenchmarkCase(
            case_id="case_06_behavioral",
            question="Describe a situation where you had a technical disagreement with a team member. How did you resolve it?",
            topic="Behavioral",
            estimated_difficulty="Medium",
            expected_topics=["STAR method", "Active listening", "Data-driven benchmark/POC", "Collaboration", "Constructive alignment"],
            evaluation_rubric=(
                "Excellent (90): Follows STAR structure, highlights active listening, objective data-driven proof (POC/benchmark), and team-first alignment.\n"
                "Good (75): Clear STAR narrative, technical trade-off evaluation, respectful resolution.\n"
                "Average (60): Describes disagreement and resolution, but lacks data-driven proof or structured narrative.\n"
                "Weak (40): Shows defensive attitude, reluctant compromise, vague resolution.\n"
                "Incorrect (15): Argued aggressively until forced to yield or manager intervened to override."
            ),
            answers=[
                BenchmarkAnswer(
                    quality_level="excellent",
                    candidate_answer=(
                        "In my previous project, a senior engineer preferred MongoDB for our analytics pipeline, whereas I advocated PostgreSQL with JSONB columns. "
                        "Instead of debating theoretically, I proposed building a quick 1-day benchmark (POC) testing both databases under our expected write/query workload. "
                        "The benchmarks showed PostgreSQL had 40% faster complex aggregation query speed while maintaining ACID guarantees needed for transaction logs. "
                        "We reviewed the benchmark data together, aligned on PostgreSQL, and completed the project on schedule."
                    ),
                    expected_scores=ExpectedScores(technical_score=90.0, communication_score=90.0, reasoning_score=90.0, confidence_score=90.0, overall_score=90.0)
                ),
                BenchmarkAnswer(
                    quality_level="good",
                    candidate_answer=(
                        "My teammate wanted to use REST for our internal microservices, but I recommended gRPC for lower latency. "
                        "We scheduled a meeting to list the pros and cons of each approach regarding payload size, serialization speed, and team familiarity. "
                        "We agreed to use gRPC for high-throughput internal services and REST for external APIs. It worked out great."
                    ),
                    expected_scores=ExpectedScores(technical_score=75.0, communication_score=80.0, reasoning_score=75.0, confidence_score=75.0, overall_score=75.0)
                ),
                BenchmarkAnswer(
                    quality_level="average",
                    candidate_answer=(
                        "I disagreed with a colleague on code architecture. He wanted monorepo and I wanted multirepo. "
                        "We talked about it, weighed opinions, and decided to go with monorepo to make sharing code easier."
                    ),
                    expected_scores=ExpectedScores(technical_score=60.0, communication_score=60.0, reasoning_score=60.0, confidence_score=60.0, overall_score=60.0)
                ),
                BenchmarkAnswer(
                    quality_level="weak",
                    candidate_answer=(
                        "My teammate wrote bad code that I didn't like. I told him his architecture was wrong. He didn't listen so I just did it my way."
                    ),
                    expected_scores=ExpectedScores(technical_score=40.0, communication_score=35.0, reasoning_score=35.0, confidence_score=40.0, overall_score=40.0)
                ),
                BenchmarkAnswer(
                    quality_level="incorrect",
                    candidate_answer=(
                        "I had a fight with my coworker about tech stack. I got angry and stopped talking to him until the engineering director forced him to do what I said."
                    ),
                    expected_scores=ExpectedScores(technical_score=15.0, communication_score=20.0, reasoning_score=10.0, confidence_score=15.0, overall_score=15.0)
                )
            ]
        ),

        # 7. Problem Solving
        BenchmarkCase(
            case_id="case_07_problem_solving",
            question="Given a large file containing 10 billion integers, how would you find the top 100 largest integers using limited memory (e.g., 100MB RAM)?",
            topic="Problem Solving",
            estimated_difficulty="Hard",
            expected_topics=["Min-Heap", "Streaming evaluation", "O(N log K) time", "O(K) space", "Memory constraint adherence"],
            evaluation_rubric=(
                "Excellent (90): Maintains Min-Heap of size 100, streams integers line-by-line, compares with root (min element), space complexity O(100) = O(1), time complexity O(N log 100).\n"
                "Good (75): Explains streaming using a min-priority queue of size 100, keeping space minimal.\n"
                "Average (60): Mentions splitting file into chunks, sorting each chunk on disk, and merging (external merge sort).\n"
                "Weak (40): Suggests loading entire file into array and calling sort() (violates 100MB memory limit).\n"
                "Incorrect (15): Claims 10B integers cannot be processed without 10B ints of RAM."
            ),
            answers=[
                BenchmarkAnswer(
                    quality_level="excellent",
                    candidate_answer=(
                        "To find the top 100 largest numbers out of 10 billion under 100MB RAM constraint, I would use a Min-Heap of size K = 100. "
                        "I stream the file line by line without loading the full file into memory. For each integer: "
                        "1) If the heap has fewer than 100 elements, push it. "
                        "2) If the integer is greater than the heap's root (the current 100th largest), pop the root and push the new integer. "
                        "Space complexity is O(K) = O(100) memory (~800 bytes), well within 100MB. Time complexity is O(N log K) = O(10B * log 100), which is highly efficient."
                    ),
                    expected_scores=ExpectedScores(technical_score=90.0, communication_score=90.0, reasoning_score=90.0, confidence_score=90.0, overall_score=90.0)
                ),
                BenchmarkAnswer(
                    quality_level="good",
                    candidate_answer=(
                        "You stream the file line by line and keep a priority queue (min-heap) of max size 100. "
                        "As you read each number, if it's larger than the min value in the queue, you replace the min value. "
                        "This uses almost zero memory and finds the top 100 numbers."
                    ),
                    expected_scores=ExpectedScores(technical_score=75.0, communication_score=80.0, reasoning_score=75.0, confidence_score=75.0, overall_score=75.0)
                ),
                BenchmarkAnswer(
                    quality_level="average",
                    candidate_answer=(
                        "Since 10 billion numbers don't fit in RAM, you split the file into smaller chunks, sort each chunk, "
                        "write them to temporary disk files, and perform an external merge sort to get the largest items."
                    ),
                    expected_scores=ExpectedScores(technical_score=60.0, communication_score=60.0, reasoning_score=60.0, confidence_score=60.0, overall_score=60.0)
                ),
                BenchmarkAnswer(
                    quality_level="weak",
                    candidate_answer=(
                        "Read the file into a Python list `numbers = file.readlines()`, convert to integers, call `numbers.sort(reverse=True)`, and return `numbers[:100]`."
                    ),
                    expected_scores=ExpectedScores(technical_score=40.0, communication_score=45.0, reasoning_score=35.0, confidence_score=40.0, overall_score=40.0)
                ),
                BenchmarkAnswer(
                    quality_level="incorrect",
                    candidate_answer=(
                        "It is impossible to process 10 billion numbers in 100MB RAM. You need at least 40GB RAM to store 10 billion 32-bit integers."
                    ),
                    expected_scores=ExpectedScores(technical_score=15.0, communication_score=25.0, reasoning_score=10.0, confidence_score=15.0, overall_score=15.0)
                )
            ]
        )
    ]
    return cases
