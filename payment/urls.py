from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_form, name='payment_form'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('config/', views.stripe_config, name='stripe-config'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('webhook/', views.stripe_webhook, name='stripe-webhook'),
]