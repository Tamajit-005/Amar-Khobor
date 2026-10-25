import os

# Tests must never reach paid APIs, even when a single file is run on its own.
os.environ["MOCK_MODE"] = "true"
