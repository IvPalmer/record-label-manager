from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RevenueAnalysisViewSet

router = DefaultRouter()
router.register(r'revenue', RevenueAnalysisViewSet, basename='revenue')

urlpatterns = [
    path('api/finances/', include(router.urls)),
]
