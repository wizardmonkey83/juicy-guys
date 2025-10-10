from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time


from .forms import GetCode
from .models import TestCase, Problem
import requests

# Create your views here.
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
                messages.error(request, "Issue finding problem")
                return render(request, "unable_to_find_problem.html")

            # TODO figure out how to allow a user to add/edit displayed testcases. right now this is fine.
            few_testcases = TestCase.objects.filter(problem=problem)[:3]

            if few_testcases:
                tokens = []
                for testcase in few_testcases:
                    stdin = testcase.input_data
                    expected_output = testcase.expected_output
                    
                    response = requests.post('http://localhost:2358/submissions', json={"source_code": source_code, "language_id": language_id, "stdin": stdin, "expected_output": expected_output})
                    data = response.json()
                    token = data["token"]
                    tokens.append(token)
                request.session["tokens"] = tokens
                # TODO pass information to frontend to begin polling check_run_results
                return render(request, "information")
            else:
                # TODO handle no testcases
                return 
        else:
            # form is invalid
            return
            

def check_run_results(request):
    tokens = request.session.get("tokens")
    # to avoid altering 'tokens' while iterating over it
    pending_tokens = tokens[:]
    if tokens:
        results = []
        while len(pending_tokens) > 0:
            for token in pending_tokens[:]:
                # "status_description" should be a valid field, but may not be =
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
                    time = data["time"]

                    results.append({
                        "stdout": stdout,
                        "stderr": stderr,
                        "status_id": status_id,
                        "status_description": status_description,
                        "language_id": language_id,
                        "time": time 
                    })
                    pending_tokens.remove(token)
                # TODO handle errors
                else:
                    messages.error(request, status_description)
                    return render(request, "reusable_fragment.html")
            # TODO this may not be the best time, check on it later.
            time.sleep(0.1)

        # to avoid going over all of this again by accident
        del request.session["tokens"]
        # TODO make an html fragment for this
        return render(request, "some web page", {"results": results})
    else:
        # TODO return an error 
        return render(request, "ur cooked")
            

