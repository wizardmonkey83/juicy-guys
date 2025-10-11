from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time


from .forms import GetCode
from .models import TestCase, Problem
import requests

# Create your views here.


# FOR RUNNING THE CODE ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# TODO make this @login_required once done testing or once user auth is set up
def process_run_code(request):
    if request.method == "POST":
        form = GetCode(request.POST)
        if form.is_valid():
            # get code
            source_code = form.cleaned_data["code"]
            problem_id = form.cleaned_data["problem_id"]
            language_id = form.cleaned_data["language_id"]

            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                # TODO figure out html fragment to be returned with error messages
                messages.error(request, "Unable to Locate Problem")
                return render(request, "problems/problem_run_response.html")

            # TODO figure out how to allow a user to add/edit displayed testcases. right now this is fine.
            few_testcases = TestCase.objects.filter(problem=problem)[:3]

            if few_testcases:
                tokens = []
                for testcase in few_testcases:
                    stdin = testcase.input_data
                    expected_output = testcase.expected_output
                    
                    response = requests.post("http://localhost:2358/submissions", json={"source_code": source_code, "language_id": language_id, "stdin": stdin, "expected_output": expected_output})
                    data = response.json()
                    token = data["token"]
                    tokens.append(token)
                request.session["tokens"] = tokens
                # TODO pass information to frontend to begin polling check_run_results. should be a button changed from "run" to "running" or an icon change
                return render(request, "information")
            else:
                messages.error(request, "No Testcases Found")
                return render(request, "problems/problem_run_response.html") 
        else:
            # form is invalid
            messages.error(request, "Invalid Form")
            return render(request, "problems/problem_run_response.html")
            
# TODO make this @login_required once done testing or once user auth is set up
def check_run_results(request):
    tokens = request.session.get("tokens")
    pending_tokens = tokens[:]
    if tokens:
        results = []
        while len(pending_tokens) > 0:
            # to avoid altering 'tokens' while iterating over it
            for token in pending_tokens[:]:
                # "status_description" should be a valid field, but may not be
                response = requests.get(f'http://localhost:2358/submissions/{token}?fields=stdout,stderr,status_id,status_description,language_id,time')
                data = response.json()
                status = data["status_id"]
                # still processing
                if status == 1 or status == 2:
                    continue
                # accepted or wrong answer
                elif status == 3 or status == 4:
                    stdout = data["stdout"]
                    stderr = data["stderr"]
                    status_id = data["status_id"]
                    status_description = data["status_description"]
                    language_id = data["language_id"]
                    execution_time = data["time"]

                    results.append({
                        "stdout": stdout,
                        "stderr": stderr,
                        "status_id": status_id,
                        "status_description": status_description,
                        "language_id": language_id,
                        "time": execution_time 
                    })
                    pending_tokens.remove(token)
                else:
                    return render(request, "problems/problem_run_response.html", {"stderr": stderr, "status_description": status_description})
            # TODO this may not be the best time, check on it later.
            time.sleep(0.1)

        # to avoid going over all of this again by accident
        del request.session["tokens"]
        # TODO make an html fragment for this
        return render(request, "problems/problem_run_response.html", {"results": results})
    else:
        messages.error(request, "Unable to Retrieve Tokens")
        return render(request, "problems/problem_run_response.html")
    
# FOR SUBMITTING THE CODE ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------







# FOR LOADING FRAGMENTS ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required
def problem_question_window(request):
    # TODO figure out redirect if user presses question twice
    return

@login_required
def problem_solution_window(request):
    # TODO figure out routing logic. all this does is change the window from the question
    return

@login_required
def problem_submissions_window(request):
    # TODO figure out routing logic. all this does is change the window from the question
    return

            

