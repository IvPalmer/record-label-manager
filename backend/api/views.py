from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from .models import (
    UserProfile, Label, Artist, Release, 
    Track, Mixtape, Document, CalendarEvent, Demo
)
from .serializers import (
    UserSerializer, UserProfileSerializer, LabelSerializer, ArtistSerializer,
    ReleaseSerializer, TrackSerializer, MixtapeSerializer, DocumentSerializer,
    CalendarEventSerializer, DemoSerializer
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own profile
        return UserProfile.objects.filter(user=self.request.user)


class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'country']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        # Users can only see labels they own or are related to
        return Label.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['labels']
    search_fields = ['name', 'project', 'country']
    ordering_fields = ['name', 'project', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Get labels owned by the user
        user_labels = Label.objects.filter(owner=user).values_list('id', flat=True)
        # Return artists associated with those labels
        return Artist.objects.filter(labels__id__in=user_labels).distinct()


class ReleaseViewSet(viewsets.ModelViewSet):
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['label', 'status']
    search_fields = ['title', 'catalog_number', 'style', 'tags']
    ordering_fields = ['title', 'release_date', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Get labels owned by the user
        user_labels = Label.objects.filter(owner=user).values_list('id', flat=True)
        # Return releases associated with those labels
        return Release.objects.filter(label__id__in=user_labels)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['release', 'artist', 'label', 'is_streaming_single']
    search_fields = ['title', 'src_code', 'tags']
    ordering_fields = ['title', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Get labels owned by the user
        user_labels = Label.objects.filter(owner=user).values_list('id', flat=True)
        # Return tracks associated with those labels
        return Track.objects.filter(label__id__in=user_labels)


class MixtapeViewSet(viewsets.ModelViewSet):
    queryset = Mixtape.objects.all()
    serializer_class = MixtapeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['artist', 'label']
    search_fields = ['title']
    ordering_fields = ['title', 'release_date', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Get labels owned by the user
        user_labels = Label.objects.filter(owner=user).values_list('id', flat=True)
        # Return mixtapes associated with those labels
        return Mixtape.objects.filter(label__id__in=user_labels)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['label']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Get labels owned by the user
        user_labels = Label.objects.filter(owner=user).values_list('id', flat=True)
        # Return documents associated with those labels
        return Document.objects.filter(label__id__in=user_labels)
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['label', 'date', 'release']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'date', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Get labels owned by the user
        user_labels = Label.objects.filter(owner=user).values_list('id', flat=True)
        # Return calendar events associated with those labels
        return CalendarEvent.objects.filter(label__id__in=user_labels)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DemoViewSet(viewsets.ModelViewSet):
    queryset = Demo.objects.all()
    serializer_class = DemoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['label', 'status']
    search_fields = ['title', 'artist_name']
    ordering_fields = ['title', 'submitted_at']
    
    def get_queryset(self):
        user = self.request.user
        # Get labels owned by the user
        user_labels = Label.objects.filter(owner=user).values_list('id', flat=True)
        # Return demos associated with those labels
        return Demo.objects.filter(label__id__in=user_labels)
    
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update the status of a demo submission."""
        demo = self.get_object()
        status = request.data.get('status')
        if status not in [choice[0] for choice in Demo.DEMO_STATUS_CHOICES]:
            return Response({"error": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)
        
        review_notes = request.data.get('review_notes', '')
        demo.status = status
        demo.review_notes = review_notes
        demo.save()
        serializer = self.get_serializer(demo)
        return Response(serializer.data)
