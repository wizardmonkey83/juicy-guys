from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time


from .forms import GetCode
from .models import TestCase, Problem, UserProblem, Language

from characters.models import Character, UserCharacter
from accounts.models import Submission
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

            language = Language.objects.get(judge0_id=language_id)
            # TODO figure out how to allow a user to add/edit displayed testcases. right now this is fine.
            few_testcases = TestCase.objects.filter(problem=problem, language=language)[:3]

            if few_testcases:
                tokens = []
                for testcase in few_testcases:
                    stdin = testcase.input_data
                    expected_output = testcase.expected_output
                    
                    response = requests.post("http://localhost:2358/submissions", json={"source_code": source_code, "language_id": language_id, "stdin": stdin, "expected_output": expected_output})
                    data = response.json()
                    token = data["token"]
                    tokens.append(
                        {"testcase_id": testcase.id,
                         "token": token}
                    )
                request.session["tokens"] = tokens
                # TODO pass information to frontend to begin polling check_run_results. should be a button changed from "run" to "running" or an icon change
                return render(request, "running.html")
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
            for item in pending_tokens[:]:
                token = item["token"]
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

                    try:
                        testcase = TestCase.objects.get(id=item["testcase_id"])

                        results.append({
                            "stdout": stdout,
                            "stderr": stderr,
                            "status_id": status_id,
                            "status_description": status_description,
                            "language_id": language_id,
                            "time": execution_time,
                            "testcase": testcase,
                        })
                        pending_tokens.remove(item)
                    except TestCase.DoesNotExist:
                        # TODO this needs to return a fragment
                        messages.error(request, "Unable to Retrieve Testcase")
                else:
                    stderr = data["stderr"]
                    status_description = data["status_description"]
                    return render(request, "problems/output_window.html", {"stderr": stderr, "status_description": status_description})
            # TODO this may not be the best time, check on it later.
            time.sleep(0.1)

        # to avoid going over all of this again by accident
        del request.session["tokens"]
        # TODO make an html fragment for this
        return render(request, "problems/output_window.html", {"results": results})
    else:
        messages.error(request, "Unable to Retrieve Tokens")
        return render(request, "problems/problem_run_response.html")
    
# FOR SUBMITTING THE CODE ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# TODO make this @login_required once done testing or once user auth is set up
def process_submit_code(request):
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
            try:
                language = Language.objects.get(judge0_id=language_id)
            except Language.DoesNotExist:
                messages.error(request, "Unable to locate language")
            testcases = TestCase.objects.filter(problem=problem, language=language)

            if testcases:
                tokens = []
                for testcase in testcases:
                    stdin = testcase.input_data
                    expected_output = testcase.expected_output
                    
                    response = requests.post("http://localhost:2358/submissions", json={"source_code": source_code, "language_id": language_id, "stdin": stdin, "expected_output": expected_output})
                    data = response.json()
                    token = data["token"]
                    tokens.append(
                        {"testcase_id": testcase.id,
                         "token": token}
                    )
                request.session["tokens"] = tokens
                request.session["problem_id"] = problem_id
                request.session["language_id"] = language_id
                request.session["code"] = source_code
                # TODO pass information to frontend to begin polling check_run_results. should be a button changed from "submit" to "submiting" or an icon change
                return render(request, "submitting.html")
            else:
                messages.error(request, "No Testcases Found")
                return render(request, "problems/problem_run_response.html") 
        else:
            # form is invalid
            messages.error(request, "Invalid Form")
            return render(request, "problems/problem_run_response.html")


def check_submit_results(request):
    tokens = request.session.get("tokens")
    problem_id = request.session.get("problem_id")
    language_id = request.session.get("language_id")
    code = request.session.get("code")

    pending_tokens = tokens[:]
    if tokens:
        results = []
        count = 0
        total_runtime = []
        total_memory = []
        while len(pending_tokens) > 0:
            # to avoid altering 'tokens' while iterating over it
            for item in pending_tokens[:]:
                token = item["token"]
                # "status_description" should be a valid field, but may not be
                response = requests.get(f'http://localhost:2358/submissions/{token}?fields=stdout,stderr,status_id,status_description,language_id,time,memory')
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
                    runtime = data["time"]
                    memory = data["memory"]

                    try:
                        testcase = TestCase.objects.get(id=item["testcase_id"])
                        
                        results.append({
                            "stdout": stdout,
                            "stderr": stderr,
                            "status_id": status_id,
                            "status_description": status_description,
                            "language_id": language_id,
                            "time": runtime,
                            "testcase": testcase,
                        })
                        pending_tokens.remove(item)
                        if status == 3:
                            count += 1
                        total_runtime.append(runtime)
                        total_memory.append(memory)
                    except TestCase.DoesNotExist:
                        # TODO this needs to return a fragment
                        messages.error(request, "Unable to Retrieve Testcase")
                else:
                    stderr = data["stderr"]
                    status_description = data["status_description"]
                    return render(request, "problems/output_window.html", {"stderr": stderr, "status_description": status_description})
            # TODO this may not be the best time, check on it later.
            time.sleep(0.1)
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            # TODO make this functional
            messages.error(request, "Unable to locate problem")

        # TODO YOU NEED TO IMPLEMENT BADGE UPDATES WHEN YOU DECIDE ON BADGES TO ADD

        language = Language.objects.get(judge0_id=language_id)

        num_of_testcases = TestCase.objects.filter(problem=problem, language=language).count()
        # if all testcases were passed (submission accepted)
        if count == num_of_testcases:
            user = request.user
            user.profile.problems_solved_count += 1
            user.profile.submissions_made_count += 1
            problem.problem_solved_count += 1
            problem.submissions_made_count += 1
            user.profile.save()
            problem.save()

            # checks to see if level up is needed. 
            try:
                # there should only be one character that meets these two filters (difficulty and category), however keep an eye on this as it may change in the future
                character = Character.objects.get(difficulty=problem.difficulty, category=problem.category)
            except Character.DoesNotExist:
                # TODO make this functional
                messages.error(request, "Unable to locate character")
            
            user_character, created = UserCharacter.objects.get_or_create(user=user, character=character)
            user_character.problems_solved_count += 1

            if user_character.problems_solved_count == 5:
                user_character.level = "bronze"
            if user_character.problems_solved_count == 10:
                user_character.level = "silver"
            if user_character.problems_solved_count == 15:
                user_character.level = "gold"
            user_character.save()

            user_problem, created = UserProblem.objects.get_or_create(problem=problem, user=user)
            user_problem.status = "solved"
            user_problem.save()

        else:
            user = request.user
            user.profile.submissions_made_count += 1
            problem.submissions_made_count += 1
            user_problem, created = UserProblem.objects.get_or_create(problem=problem, user=user)
            # might be redundant
            if user_problem.status != "solved":
                user_problem.status == "attempted"

            user_problem.save()
            user.profile.save()
            problem.save()

        if total_runtime:
            avg_runtime = sum(total_runtime) / len(total_runtime)
        else:
            avg_runtime = 0
        if total_memory:
            avg_memory = sum(total_memory) / len(total_memory)
        else:
            avg_memory = 0

        if count == num_of_testcases:
            Submission.objects.create(
                user=user,
                problem=problem,
                language=language,
                code=code,
                testcases_passed=count,
                num_of_testcases=num_of_testcases,
                status="accepted",
                runtime=avg_runtime,
                memory=avg_memory,
            )
        else:
            Submission.objects.create(
                user=user,
                problem=problem,
                language=language,
                code=code,
                testcases_passed=count,
                num_of_testcases=num_of_testcases,
                status="wrong_answer",
                runtime=avg_runtime,
                memory=avg_memory,
            )
        # so that tokens dont interfere with other processes
        del request.session["tokens"]
        del request.session["problem_id"]
        del request.session["language_id"]
        del request.session["code"]
        # TODO make an html fragment for this
        return render(request, "problems/output_window.html", {"results": results})
    else:
        messages.error(request, "Unable to Retrieve Tokens")
        return render(request, "problems/problem_run_response.html")



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

            

