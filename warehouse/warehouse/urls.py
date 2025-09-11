from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler403


urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls',namespace='account')),
    path('ordercart/', include('ordercart.urls', namespace='ordercart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('', include('mebel.urls', namespace='mebel')),
    path('__debug__/', include('debug_toolbar.urls')),

]

handler403 = 'account.views.custom_permission_denied_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

