"""
URL configuration for ScanNifty100
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.web.apps.companies.views import home


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('companies/', include('apps.web.apps.companies.urls', namespace='companies')),
    path('sectors/', include('apps.web.apps.sectors.urls', namespace='sectors')),
    path('screener/', include('apps.web.apps.web.urls')),
    path('api/', include('apps.web.apps.api.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
