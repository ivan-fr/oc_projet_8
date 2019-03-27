from . import views
from django.urls import path, re_path
from django.contrib.auth import views as auth_views

app_name = "purbeurre"

# define url of purbeurre website
urlpatterns = [
    path('', views.GeneralView.index, name='index'),
    path('credits/', views.GeneralView.show_credits, name='credits'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    re_path(r'^substitutes/'
            r'for_replace/(?P<bar_code>[\d]+)/$',
            views.GeneralView.get_substitutes,
            name='substitutes'),
    re_path(r'^create_link/(?P<sign>[-\w:]+)/'
            r'substitute_choice/(?P<substitute_bar_code>[\d]+)/$',
            views.GeneralView.create_substitute_link, name='create_link'),
    re_path(r'^product/(?P<_id>[\d]+)/$', views.GeneralView.show_product,
            name='show_product'),
    path('my_products/', views.GeneralView.show_user_link, name='my_products'),
    path('my_account/', views.GeneralView.profile, name='profile'),
]
