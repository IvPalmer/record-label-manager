from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    UserViewSet, UserProfileViewSet, LabelViewSet, ArtistViewSet,
    ReleaseViewSet, TrackViewSet, MixtapeViewSet, DocumentViewSet,
    CalendarEventViewSet, DemoViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'labels', LabelViewSet)
router.register(r'artists', ArtistViewSet)
router.register(r'releases', ReleaseViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'mixtapes', MixtapeViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'calendar', CalendarEventViewSet)
router.register(r'demos', DemoViewSet)

urlpatterns = [
    # API endpoints using router
    path('', include(router.urls)),
    
    # JWT Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
