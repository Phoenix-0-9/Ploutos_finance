import os
# Ensure config.py does not raise on missing API key during tests.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-key-for-ci-do-not-use")
