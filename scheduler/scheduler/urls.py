"""scheduler URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path

from scheduler_app import views # type: ignore

urlpatterns = [
    path('', views.HomepageView.as_view()),
    path('admin/', admin.site.urls),
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('users/', views.ListUsersView.as_view()),
    path('users/create/', views.CreateUserView.as_view()),
    path('users/<int:account>/', views.ViewUserView.as_view()),
    path('users/<int:account>/delete/', views.DeleteUserView.as_view()),
    path('courses/', views.ListCoursesView.as_view()),
    path('courses/create/', views.CreateCourseView.as_view()),
    path('courses/<int:course>/', views.ViewCourseView.as_view()),
    path('courses/<int:course>/edit/', views.EditCourseView.as_view()),
    path('courses/<int:course>/delete/', views.DeleteCourseView.as_view()),
    path('courses/<int:course>/sections/<int:section>/delete/', views.DeleteSectionView.as_view()),
    path('courses/<int:course>/assign/', views.AssignToCourseview.as_view()),
    path('courses/<int:course>/assign/instructor/', views.AssignInstructorview.as_view()),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
