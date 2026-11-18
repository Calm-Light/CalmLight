# Read by gunicorn automatically (it looks for ./gunicorn.conf.py), so the Render start command doesn't change.
# The default worker timeout is 30 s, the same as smart add's AI read timeout (meds.ai.TIMEOUT_SECONDS), so a slow
# AI answer got killed by gunicorn and Render showed a 502 page. 60 s leaves a margin over the AI timeouts.
timeout = 60
