from django.urls import path
from user import views

from .views import  create_shop_request  # Import the new view

app_name='user'
urlpatterns = [
    
    path('indexfish/', views.indexfish, name='indexfish'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('profile_completion/', views.profile_completion, name='profile_completion'),
    path('profile_view/', views.profile_view, name='profile_view'),
    path('profile_update/', views.profile_update, name='profile_update'), 
    path('create-shop-request/', create_shop_request, name='create_shop_request'),  # Add this line
    path('shopdetails/<int:id>/', views.ShopDetailView.as_view(), name='shop_detail'), 
    
      # URL for shop details
    
    path('dashboard-content/', views.dashboard_content, name='dashboard_content'),
    path('order-history/', views.order_history, name='order_history'),
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
]
