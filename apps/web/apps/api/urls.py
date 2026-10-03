"""
API URL routing.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import CompanyViewSet, DataQualityView, MetricViewSet, RankingViewSet, SectorViewSet

router = DefaultRouter()
router.register(r'v1/companies', CompanyViewSet, basename='company')
router.register(r'v1/sectors', SectorViewSet, basename='sector')
router.register(r'v1/metrics', MetricViewSet, basename='metric')
router.register(r'v1/rankings', RankingViewSet, basename='ranking')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('v1/data-quality/', DataQualityView.as_view(), name='data-quality'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
]
