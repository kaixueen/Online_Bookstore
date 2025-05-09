from django.db import connection

class SetSessionContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = None
        if request.user.is_authenticated:
            self.set_session_context(request)
        response = self.get_response(request)
        return response

    def set_session_context(self, request):
        user = request.user
        role = 'unknown'
        user_id = None
        is_staff = 1 if user.is_staff else 0

        if user.is_superuser:
            role = 'admin'
        elif hasattr(user, 'sellerprofile'):
            role = 'seller'
            user_id = user.id
        elif hasattr(user, 'customerprofile'):
            role = 'customer'
            user_id = user.id

        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_set_session_context @key=N'role', @value=%s;", [role])
            cursor.execute("EXEC sp_set_session_context @key=N'is_staff', @value=%s;", [is_staff])
            if user_id:
                cursor.execute("EXEC sp_set_session_context @key=N'user_id', @value=%s;", [str(user_id)])

