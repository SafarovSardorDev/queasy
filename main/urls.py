from django.urls import path
from .views import index, signup, ready_to_test, download_test_pdf, test, checktest, new_test, new_question, profile
urlpatterns = [
    path('', index, name='index'),
    path('<int:test_id>/ready_to_test', ready_to_test, name="ready_to_test"),
    path('<int:test_id>/test', test, name="test"),
    path('<int:checktest_id>/checktest', checktest, name="checktest"),
    path('download-test/<int:test_id>/pdf/', download_test_pdf, name='download_test_pdf'),
    path('new_test', new_test, name="new_test"),
    path('<int:test_id>/new_question', new_question, name="new_question"),
    path('<int:user_id>/profile', profile, name="profile"),
    path('signup', signup, name='signup'),
]