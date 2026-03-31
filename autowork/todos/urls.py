from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from todos.views import CategoryViewSet, LogoutView, RegisterView, TodoViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"todos", TodoViewSet, basename="todo")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", obtain_auth_token, name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
] + router.urls
