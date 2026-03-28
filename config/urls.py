from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.home.views import health_check, faq_publique, contact_public

urlpatterns = [
    path('health/',  health_check,   name='health'),
    path('faq/',     faq_publique,   name='faq'),
    path('contact/', contact_public, name='contact'),
    path('',            include('apps.home.urls')),
    path('admin/',                   admin.site.urls),
    path('api/auth/',                include('apps.accounts.urls')),
    path('api/admin/',               include('apps.api_admin.urls')),
    path('api/products/',            include('apps.catalog.urls')),
    path('api/stock/',               include('apps.stock.urls')),
    path('api/orders/',              include('apps.orders.urls')),
    path('api/payments/',            include('apps.payments.urls')),
    path('api/collectes/',           include('apps.collectes.urls')),
    path('api/geo/',                 include('apps.geo.urls')),
    path('',            include('apps.core.urls')),
    path('analytics/',               include('apps.analytics.urls')),
    path('api/schema/',              SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/',        SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
