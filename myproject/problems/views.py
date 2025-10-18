from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Subquery
import time
import datetime


from .forms import GetCode, PassProblemID
from .models import TestCase, Problem, UserProblem, Language

from characters.models import Character, UserCharacter
from accounts.models import Submission, Badge
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

            try:
                language = Language.objects.get(judge0_id=language_id)
            except Language.DoesNotExist:
                messages.error(request, "Unable to locate language")
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
# this function gets polled repeatedly by the frontend
def check_run_results(request):
    tokens = request.session.get("tokens")
    pending_tokens = tokens[:]
    if tokens:
        results = []
        finished_testcases = 0
        for item in pending_tokens:
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
                    finished_testcases += 1
                except TestCase.DoesNotExist:
                    # TODO this needs to return a fragment
                    messages.error(request, "Unable to Retrieve Testcase")
            else:
                stderr = data["stderr"]
                status_description = data["status_description"]
                return render(request, "problems/output_window.html", {"stderr": stderr, "status_description": status_description})
        
        # TODO make an html fragment for this
        if finished_testcases == len(pending_tokens):
            del request.session["tokens"]
            return render(request, "problems/output_window.html", {"results": results})
        else:
            # keep polling
            return render(request, "running.html")
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
        correct = 0
        finished_testcases = 0
        total_runtime = []
        total_memory = []
        # TODO fix this --> i think that you are iterating over all testcases, even if they have already been completed. this will be a major waste of time. 
        for item in pending_tokens:
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
                    if status == 3:
                        correct += 1
                    total_runtime.append(runtime)
                    total_memory.append(memory)
                    finished_testcases += 1
                except TestCase.DoesNotExist:
                    # TODO this needs to return a fragment
                    messages.error(request, "Unable to Retrieve Testcase")
            else:
                # runtime error 
                stderr = data["stderr"]
                status_description = data["status_description"]
                return render(request, "problems/output_window.html", {"stderr": stderr, "status_description": status_description})
            
        # submission completed (all testcases tested)  
        if finished_testcases == len(pending_tokens):

            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                # TODO make this functional
                messages.error(request, "Unable to locate problem")
            try:
                language = Language.objects.get(judge0_id=language_id)
            except Language.DoesNotExist:
                messages.error(request, "Unable to locate language")

            num_of_testcases = TestCase.objects.filter(problem=problem, language=language).count()
            # if all testcases were passed (submission accepted)
            if correct == num_of_testcases:
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
                    user_problem.status = "attempted"

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

            if correct == num_of_testcases:
                # this might work. submission is referenced below
                Submission.objects.create(
                    user=user,
                    problem=problem,
                    language=language,
                    code=code,
                    testcases_passed=correct,
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
                    testcases_passed=correct, 
                    num_of_testcases=num_of_testcases,
                    status="wrong_answer",
                    runtime=avg_runtime,
                    memory=avg_memory,
                )
            # GOAT badge (messi)
            if user.profile.acceptance_rate >= .95:
                # this will return an error until i create the badge
                badge = Badge.objects.get(title="GOAT")
                if user.profile.badges.filter(id=badge.id).exists():
                    # i think this is correct....
                    pass
                else:
                    user.profile.badges.add(badge)
            # ENOC badge (ozuna). for now its solving all problems, except legendary. should probably change
            if user.profile.problems_solved_count == Problem.objects.filter(Q(difficulty="easy") | Q(difficulty="medium") | Q(difficulty="hard")).count():
                badge = Badge.objects.get(title="ENOC")
                if user.profile.badges.filter(id=badge.id).exists():
                    pass
                else:
                    # cant use += for ManyToMany relationships
                    user.profile.badges.add(badge)
            # BATMAN badge (solve problem between 12am and 5am)
            now = datetime.time.now()
            midnight = datetime.time(00, 00, 00)
            five_am = datetime.time(5, 00, 00)
            if now >= midnight and now <= five_am:
                badge = Badge.objects.get(title="Batman")
                if user.profile.badges.filter(id=badge.id).exists():
                    pass
                else:
                    user.profile.badges.add(badge)
            # MASTER CHIEF (solve a legendary problem)
            if problem.difficulty == "legendary" and correct == num_of_testcases:
                badge = Badge.objects.get(title="Master Chief")
                if user.profile.badges.filter(id=badge.id).exists():
                    pass
                else:
                    user.profile.badges.add(badge)
            # AVATAR master an element (solve all problems in a category)
            all_problems_in_category_count = Problem.objects.filter(category=problem.category).count()
            solved_problems_count = UserProblem.objects.filter(problem__category=problem.category, status="solved", user=user).count()
            # this may be a bad way of determining solved problems in a certain category
            if all_problems_in_category_count == solved_problems_count:
                badge = Badge.objects.get(title="Avatar")
                if user.profile.badges.filter(id=badge.id).exists():
                    pass
                else:
                    user.profile.badges.add(badge)

            # so that tokens dont interfere with other processes
            del request.session["tokens"]
            del request.session["problem_id"]
            del request.session["language_id"]
            del request.session["code"]
            # TODO make an html fragment for this
            return render(request, "problems/output_window.html", {"results": results})

        else:
            # keep polling
            return render(request, "running.html")
    
    else:
        messages.error(request, "Unable to Retrieve Tokens")
        return render(request, "problems/problem_run_response.html")



# FOR LOADING FRAGMENTS ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required
def problem_list_window(request):
    user = request.user
    all_problems_with_status = Problem.objects.annotate(solution_status=Subquery(UserProblem.objects.all().values("status").annotate(status))

@login_required
def load_problem(request):
    if request.method == "POST":
        form = PassProblemID(request.POST)
        if form.is_valid():
            problem_id = form.cleaned_data["problem_id"]
            try:
                problem = Problem.objects.get(id=problem_id)



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

            

