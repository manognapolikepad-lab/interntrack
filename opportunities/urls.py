from django.urls import path

from . import views

urlpatterns = [
    path("", views.opportunity_list, name="opportunity_list"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("tracker/", views.tracker, name="tracker"),
    path("saved/", views.saved_opportunities, name="saved_opportunities"),
    path("profile/", views.profile, name="profile"),
    path("opportunity/<int:pk>/", views.opportunity_detail, name="opportunity_detail"),
    path("opportunity/<int:pk>/apply/", views.add_application, name="add_application"),
    path("opportunity/<int:pk>/save/", views.toggle_saved, name="toggle_saved"),
    path("application/<int:pk>/update/", views.update_application, name="update_application"),
]