from django.urls import path
from . import views

urlpatterns = [
    path("", views.payment_form, name="payment_form"),
    path("checkout/", views.MpesaCheckout.as_view(), name="checkout"),
    path("callback/", views.MpesaCallBack.as_view(), name="callback"),
    path("stk-query/", views.MpesaStkQuery.as_view(), name="stk_query"),
    path("status/<str:checkout_request_id>/", views.transaction_status, name="transaction_status"),
]