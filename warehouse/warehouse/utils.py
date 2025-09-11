from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

def group_required(*group_names):
    """Требует членства пользователя хотя бы в одной из переданных групп."""
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if not request.user.groups.filter(name__in=group_names).exists():
                return HttpResponseForbidden("У вас нет прав для выполнения этого действия.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Конкретные декораторы для наших групп
def managers_required(view_func):
    return group_required('Менеджеры')(view_func)

def mto_required(view_func):
    return group_required('Отдел МТО')(view_func)