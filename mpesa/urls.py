from django.urls import path
from . import views

urlpatterns = [
    path("checkout/", views.MpesaCheckout.as_view(), name="checkout"),
    path("callback/", views.MpesaCallBack.as_view(), name="callback"),
    path("query/", views.MpesaStkQuery.as_view(), name="stk_query")
]