from django.urls import path
from .views import process_run_code, check_run_results, check_submit_results, process_submit_code, problem_problem_window, problem_solution_window, problem_submissions_window, load_problem, problem_list_window, search_for_problem, filter_problem_difficulty, problem_output_window, problem_testcase_window

urlpatterns = [
    # problem list page
    path("problems/", problem_list_window, name="problem_list_window"),
    path("problems/search/", search_for_problem, name="search_for_problem"),
    path("problems/filter-difficulty/", filter_problem_difficulty, name="filter_problem_difficulty"),
    # loads specific problem page
    path("problems/<int:problem_id>/", load_problem, name="load_problem"),

    # performs execution (running/submission of code)
    path("problems/problem/run", process_run_code, name="process_run_code"),
    path("problems/problem/submit", process_submit_code, name="process_submit_code"),

    # polls views to see if code has finished evaluation
    path("problems/running/", check_run_results, name="check_run_results"),
    path("problems/submitting/", check_submit_results, name="check_submit_results"),

    # routing for buttons inside of the problem panel
    path("problems/problem-problem-window/", problem_problem_window, name="problem_problem_window"),
    path("problems/problem-solution-window/", problem_solution_window, name="problem_solution_window"),
    path("problems/problem-submissions-window/", problem_submissions_window, name="problem_submissions_window"),

    # routing for buttons (testcase, output) inside of the console
    path("problems/problem-testcase-window/", problem_testcase_window, name="problem_testcase_window"),
    path("problems/problem-output-window/", problem_output_window, name="problem_output_window"),
]