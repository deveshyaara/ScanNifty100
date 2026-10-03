from django.urls import path
from .views import screener

app_name = 'web'

urlpatterns = [
    path('', screener, name='screener'),
]
