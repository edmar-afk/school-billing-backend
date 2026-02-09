from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
# ssd
urlpatterns = [
    # path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('register/', views.RegisterView.as_view(), name='register'),
   
   path("students/", views.StudentListView.as_view(), name="student-list"),
   path("students/create/", views.StudentCreateView.as_view(), name="student-create"),
   path("students/", views.StudentListView.as_view(), name="student-list"),
   path("students/<int:id>/update/", views.StudentUpdateView.as_view()),
   path("students/delete/<int:id>/", views.StudentDeleteView.as_view(), name="student-delete"),
   
   
   path("billing/create/", views.BillingCreateView.as_view(), name="billing-create"),
   path("billings/", views.BillingLists.as_view(), name="billing-lists"),
   path("billing/<int:id>/pay/", views.BillingPaymentUpdateView.as_view()),
   path("billing/delete/<int:id>/", views.BillingDeleteView.as_view(), name="billing-delete"),
   
   path("send-billing-email/<int:billing_id>/", views.SendBillingEmailView.as_view()),
   
   path("students/count/", views.StudentCountView.as_view(), name="student-count"),
   path("billing/total-paid/", views.TotalPaidAmountView.as_view()),
   
   path('mail/count/', views.MailSentCountView.as_view(), name='mail-sent-count'),
   path('billing/export-excel/', views.BillingExcelExportView.as_view()),
   
   path('billings/paid/', views.PaidBillingListView.as_view()),
]
