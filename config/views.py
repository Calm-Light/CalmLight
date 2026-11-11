from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Health check for the hosting platform: 200 if the database answers."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "error", "database": "unreachable"}, status=503)
    return JsonResponse({"status": "ok"})
