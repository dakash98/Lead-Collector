from django.urls import path
from leads import views
# from apis import apis

app_name = 'leads'
urlpatterns = [
    path('', views.ListUsers.as_view(), name='index'),
    path('retrieve-leads/<int:page_no>/', views.FetchLeads.as_view(), name='fetch-leads'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
]