# Read by gunicorn automatically (it looks for ./gunicorn.conf.py), so the Render start command doesn't change.
# The default worker timeout is 30 s. Smart add waits up to meds.ai.TIMEOUT_SECONDS for the AI, so give the
# worker more time than that: otherwise gunicorn kills a slow request and Render shows a 502 page.
timeout = 60
