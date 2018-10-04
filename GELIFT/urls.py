from django.conf import settings
from django.conf.urls.static import static

from backend.urls import urlpatterns as backend_url
from webapp.urls import urlpatterns as webapp_url

urlpatterns = []
urlpatterns += backend_url
urlpatterns += webapp_url
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
