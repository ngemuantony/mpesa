"""
URL configuration for config project.


"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('payments/', include('mpesa.urls'))
]
