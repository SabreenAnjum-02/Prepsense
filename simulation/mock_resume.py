import os

# We will just write a dummy text file to act as the "mock resume" for the agent to parse.
def get_mock_resume_path() -> str:
    """Creates a temporary mock resume file and returns its path."""
    import tempfile
    
    mock_content = (
        "John Doe\n"
        "Software Engineer\n"
        "Skills: Python, React, AWS, Docker\n"
        "Experience: 5 years at TechCorp building scalable backends.\n"
    )
    
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, 'w') as f:
        f.write(mock_content)
        
    return path
