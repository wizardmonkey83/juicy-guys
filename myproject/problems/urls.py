from django.urls import path
from .views import process_run_code, problem_question_window, problem_solution_window, problem_submissions_window, load_problem

urlpatterns = [
    path("problems/<int:problem_id>/", load_problem, name="load_problem")

    # performs execution (running and submission of code)
    path("problems/problem/run", process_run_code, name="process_run_code"),

    # routing for buttons inside of the problem panel
    path("problems/problem-question-window/", problem_question_window, name="problem_question_window"),
    path("problems/problem-solution-window/", problem_solution_window, name="problem_solution_window"),
    path("problems/problem-submissions-window/", problem_submissions_window, name="problem_submissions_window"),
]