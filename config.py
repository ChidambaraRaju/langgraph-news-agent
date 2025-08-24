# config.py

# The list of topics for a general news request
GENERAL_TOPICS = [
    "World News", 
    "India National News", 
    "Business & Economy", 
    "Technology", 
    "Sports"
]

# The LLM models you want to use for different tasks
# Using a powerful model for the main logic
MAIN_LLM_MODEL = "moonshotai/kimi-k2-instruct" 
# Using a powerful model for the final creative writing task
NEWSPAPER_CREATOR_LLM_MODEL = "openai/gpt-oss-120b"