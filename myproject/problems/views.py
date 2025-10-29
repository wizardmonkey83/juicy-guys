from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q, Subquery, OuterRef, Prefetch
import time
import datetime
import json
import textwrap
import ast


from .forms import GetCode, SearchForProblem, FilterProblemDifficulty, PassProblemID, FilterCategories
from .models import TestCase, Problem, UserProblem, Language, Category, Quote, Example, Hint, Solution, SolutionCode, ExampleTestcase, ProblemCode

from characters.models import Character, UserCharacter
from accounts.models import Submission, Badge
import requests

# Create your views here.


# RUNNING THE CODE ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required
def process_run_code(request):
    if request.method == "POST":
        form = GetCode(request.POST)
        if form.is_valid():
            # get code
            source_code = form.cleaned_data["code"]
            problem_id = form.cleaned_data["problem_id"]
            language_id = form.cleaned_data["language_id"]
            custom_testcases = form.cleaned_data["custom_testcases"]

            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                # TODO figure out html fragment to be returned with error messages
                messages.error(request, "Unable to Locate Problem")
                return render(request, "problems/page/problem_run_response.html")
            # this should work
            few_testcases = json.loads(custom_testcases)

            if few_testcases:
                tokens = []
                for testcase in few_testcases:

                    # script to prep submission for judge0
                    scaffolding_imports = "import sys\nimport json\nfrom typing import List, Dict, Set, Tuple, Optional\n"
                    class_name = problem.class_name
                    method_name = problem.method_name
                    parameter_names = problem.parameter_names
                    # usuing .get() instead of dict["key"] so a keyerror isnt raised if value is not present
                    stdin_string = testcase.get("input")
                    expected_output = testcase.get("output")
                    # print(f"STDIN_STRING: {stdin_string}")

                    try:
                        # the frontend renders the default stdin using single quotes, invalidating the JSON structure. this is then passed back here and the script tries to parse it but fails. this should fix it
                        stdin_dict = ast.literal_eval(stdin_string)
                    except (ValueError, SyntaxError):
                        try:
                            # problably already valid JSON
                            stdin_dict = json.loads(stdin_string)
                        except json.JSONDecodeError:
                            # ggeez
                            pass
                    # when the "run" button is pressed twice, for some reason its sending the json back with extra backslashes. this might fix it 
                    if isinstance(stdin_dict, str):
                        try:
                            stdin_dict = json.loads(stdin_string)
                        except json.JSONDecodeError:
                            stdin_dict = ast.literal_eval(stdin_string)

                    # print(f"STDIN_DICT: {stdin_dict}")
                    # textwrap solves indentation error
                    # instance creates the instance of the solution class
                    driver_script = textwrap.dedent(f"""
                    try:
                        data = json.loads(sys.stdin.read())
                        instance = {class_name}()
                        method_to_call = getattr(instance, "{method_name}")
                        result = method_to_call(**data)
                        print(result)
                    except Exception as error:
                        print(f"Execution error: {{error}}", file=sys.stderr)
                    """)
                    full_script_string  = scaffolding_imports + "\n" + source_code + "\n" + driver_script
                    valid_stdin_json = json.dumps(stdin_dict)
                    payload = {"source_code": full_script_string, "language_id": language_id, "stdin": valid_stdin_json, "expected_output": expected_output}

                    
                    response = requests.post("http://159.203.137.178:2358/submissions", json=payload)
                    data = response.json()
                    token = data["token"]
                    tokens.append(
                        {"token": token,
                         "stdin": valid_stdin_json,
                         "expected_output": expected_output}
                    )
                request.session["tokens"] = tokens
                request.session["run_language_id"] = language_id
                # the url needs a problem object as an argument
                request.session["problem_id"] = problem_id
                # TODO pass information to frontend to begin polling check_run_results. should be a button changed from "run" to "running" or an icon change
                return render(request, "problems/page/running.html")
            else:
                messages.error(request, "No Testcases Found")
                return render(request, "problems/page/problem_run_response.html") 
        else:
            # form is invalid
            errors = form.errors
            messages.error(request, f"Errors: {errors}")
            return render(request, "problems/page/problem_run_response.html")
    else:
        # method is invalid
        messages.error(request, "Invalid Request Method")
        return render(request, "problems/page/problem_run_response.html")
            

# this function gets polled repeatedly by the frontend
@login_required
def check_run_results(request):
    tokens = request.session.get("tokens")
    language_id = request.session.get("run_language_id")
    # the url needs a problem object as an argument
    problem_id = request.session.get("problem_id")

    try:
        problem = Problem.objects.get(id=problem_id)
    except Problem.DoesNotExist:
        messages.error(request, "Unable to locate problem")

    if tokens:
        pending_tokens = tokens[:]
        results = []
        finished_testcases = 0
        correct = 0
        for item in pending_tokens:
            token = item["token"]
            stdin = item["stdin"]
            expected_output = item["expected_output"]
            # "status_description" should be a valid field, but may not be
            response = requests.get(f'http://159.203.137.178:2358/submissions/{token}')
            data = response.json()
            # print(f"JUDGE0 RESPONSE: {data}")
            status = data["status"]["id"]
            # still processing
            if status == 1 or status == 2:
                continue
            # accepted or wrong answer
            elif status == 3 or status == 4:
                stdout = data["stdout"]
                stderr = data["stderr"]
                status_id = data["status"]["id"]
                status_description = data["status"]["description"]
                execution_time = data["time"]

                results.append({
                    "stdin": stdin,
                    "expected_output": expected_output,
                    "stdout": stdout,
                    "stderr": stderr,
                    "status_id": status_id,
                    "status_description": status_description,
                    "language_id": language_id,
                    "time": execution_time,
                    
                })
                if status == 3:
                    correct += 1
                finished_testcases += 1
            else:
                stderr = data["stderr"]
                status_description = data["status"]["description"]
                return render(request, "problems/page/output_window.html", {"stdin": stdin, "expected_output": expected_output, "stderr": stderr, "status_description": status_description, "language_id": language_id, "problem": problem})
        
        if finished_testcases == len(pending_tokens):
            del request.session["run_language_id"]
            del request.session["tokens"]
            del request.session["problem_id"]
            if correct == finished_testcases:
                passed_testcases = f"{correct}/{finished_testcases}"
                # print(f"FINISHED RESULTS: {results}")
                return render(request, "problems/page/output_window.html", {"results": results, "overall_status": "Accepted", "passed_testcases": passed_testcases, "problem": problem})
            else:
                passed_testcases = f"{correct}/{finished_testcases}"
                return render(request, "problems/page/output_window.html", {"results": results, "overall_status": "Wrong Answer", "passed_testcases": passed_testcases, "problem": problem})
        else:
            # keep polling
             # print(f"ELSE RESULTS: {results}")
            return HttpResponse(status=204)
    else:
        # one last poll is made when the evaluation stops, "status=204" stops a blank rendering
        return HttpResponse(status=204)
    
# FOR SUBMITTING THE CODE ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
def process_submit_code(request):
    if request.method == "POST":
        form = GetCode(request.POST)
        if form.is_valid():
            # get code
            source_code = form.cleaned_data["code"]
            problem_id = form.cleaned_data["problem_id"]
            language_id = form.cleaned_data["language_id"]
            print(f"LANGUAGE_ID: {language_id}")

            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                # TODO figure out html fragment to be returned with error messages
                messages.error(request, "Unable to Locate Problem")
                return render(request, "problems/page/problem_run_response.html")
            try:
                language = Language.objects.get(judge0_id=language_id)
            except Language.DoesNotExist:
                messages.error(request, "Unable to locate language")
                return render(request, "problems/page/problem_run_response.html")

            class_name = problem.class_name
            method_name = problem.method_name
            parameter_names = problem.parameter_names

            # the language filter ay not actually be necessary. double check
            testcases = TestCase.objects.filter(problem=problem, language=language)

            if testcases:
                tokens = []
                for testcase in testcases:
                    stdin_dict = testcase.input_data
                    expected_output = testcase.expected_output

                    # script to prep submission for judge0
                    scaffolding_imports = "import sys\nimport json\nfrom typing import List, Dict, Set, Tuple, Optional\n"
                    class_name = problem.class_name
                    method_name = problem.method_name

                    driver_script = textwrap.dedent(f"""
                    try:
                        data = json.loads(sys.stdin.read())
                        instance = {class_name}()
                        method_to_call = getattr(instance, "{method_name}")
                        result = method_to_call(**data)
                        print(result)
                    except Exception as error:
                        print(f"Execution error: {{error}}", file=sys.stderr)
                    """)
                    full_script_string  = scaffolding_imports + "\n" + source_code + "\n" + driver_script
                    valid_stdin_json = json.dumps(stdin_dict)
                    payload = {"source_code": full_script_string, "language_id": language_id, "stdin": valid_stdin_json, "expected_output": expected_output}
                    
                    response = requests.post("http://159.203.137.178:2358/submissions", json=payload)
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
                return render(request, "problems/page/submitting.html")
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
            response = requests.get(f'http://159.203.137.178:2358/submissions/{token}')
            data = response.json()
            status = data["status"]["id"]
            # still processing
            if status == 1 or status == 2:
                continue
            # accepted or wrong answer
            elif status == 3 or status == 4:
                stdout = data["stdout"]
                stderr = data["stderr"]
                status_id = data["status"]["id"]
                status_description = data["status"]["description"]
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
                status_description = data["status"]["description"]
                return render(request, "problems/page/output_window.html", {"stderr": stderr, "status_description": status_description})
            
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

            context = {
                "results": results,
                "submission_was_successful": True,
                "problem": problem,
                "language_id": language.judge0_id
            }
            return render(request, "problems/page/output_window.html", context)

        else:
            # keep polling
            return HttpResponse(status=204)
    
    else:
        return HttpResponse(status=204)



# FOR LOADING FRAGMENTS/PAGES ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
def problem_list_window(request):
    user = request.user

    categories = Category.objects.all()
    # random quote
    quote = Quote.objects.order_by("?").first()
    # subqueries are essentially just like @property for views
    # OuterRef makes sure the problem is the same between UserProblem and Problem. [:1] makes sure only one status per problem is returned, shouldnt be an issue but why not.
    user_status_subquery = UserProblem.objects.filter(problem=OuterRef("pk"), user=user).values("status")[:1]
    all_problems = Problem.objects.annotate(user_status=Subquery(user_status_subquery))

    return render(request, "problems/list/problem_list.html", {"problems": all_problems, "categories": categories, "quote": quote})



@login_required
def load_problem(request, problem_id):
    if request.method == "GET":
        # realistically if this doesnt work the site is cooked
        try:
            user = request.user
            problem = Problem.objects.get(id=problem_id)
            # will return code for all languages, template can parse through
            problem_codes = ProblemCode.objects.filter(problem=problem)
            user_problem, created = UserProblem.objects.get_or_create(user=user, problem=problem)
            # TODO ExampleTestcase should fix the testcase issue (allocating certain testcases for certain problems)
            testcases = ExampleTestcase.objects.filter(problem=problem)
            examples = Example.objects.filter(problem=problem)
            hints = Hint.objects.filter(problem=problem)
        except Problem.DoesNotExist:
            messages.error(request, "Unable to locate problem")
        return render(request, "problems/page/problem_page.html", {"problem": problem, "problem_codes": problem_codes, "user_problem": user_problem, "testcases": testcases, "examples": examples, "hints": hints})
    
        
@login_required
def search_for_problem(request):
    if request.method == "POST":
        form = SearchForProblem(request.POST)
        if form.is_valid():
            query = form.cleaned_data["query"]
            problems = Problem.objects.filter(title__icontains=query)
            return render(request, "problems/list/search_problems_fragment.html", {"problems": problems})
    return HttpResponse("")

@login_required
def filter_problem_difficulty(request):
    if request.method == "POST":
        form = FilterProblemDifficulty(request.POST)
        if form.is_valid():
            difficulty = form.cleaned_data["difficulty"]
            user = request.user
            if difficulty == "all":
                user_status_subquery = UserProblem.objects.filter(problem=OuterRef("pk"), user=user).values("status")[:1]
                problems = Problem.objects.annotate(user_status=Subquery(user_status_subquery))
                return render(request, "problems/list/search_problems_fragment.html", {"problems": problems})
            else:
                user_status_subquery = UserProblem.objects.filter(problem=OuterRef("pk"), user=user).values("status")[:1]
                problems = Problem.objects.filter(difficulty=difficulty).annotate(user_status=Subquery(user_status_subquery))
                return render(request, "problems/list/search_problems_fragment.html", {"problems": problems})
    return HttpResponse("")



@login_required
def problem_problem_window(request):
    if request.method == "POST":
        form = PassProblemID(request.POST)
        if form.is_valid():
            problem_id = form.cleaned_data["problem_id"]
            try:
                user = request.user
                problem = Problem.objects.get(id=problem_id)
                user_problem, created = UserProblem.objects.get_or_create(user=user, problem=problem)
                # TODO ExampleTestcase should fix the testcase issue (allocating certain testcases for certain problems)
                testcases = ExampleTestcase.objects.filter(problem=problem)
                examples = Example.objects.filter(problem=problem)
                hints = Hint.objects.filter(problem=problem)
            except Problem.DoesNotExist:
                messages.error(request, "Unable to locate problem")
            return render(request, "problems/page/problem_window.html", {"problem": problem, "user_problem": user_problem, "testcases": testcases, "examples": examples, "hints": hints})

@login_required
def problem_solution_window(request):
    if request.method == "POST":
        form = PassProblemID(request.POST)
        if form.is_valid():
            problem_id = form.cleaned_data["problem_id"]
            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                messages.error(request, "Unable to locate problem")
                

            # links the solution code with the solution. kinda like a subquery but for a whole model
            solutions = Solution.objects.filter(problem=problem).prefetch_related("codes")

            return render(request, "problems/page/solution_window.html", {"solutions": solutions})

@login_required
def problem_submissions_window(request):
    if request.method == "POST":
        form = PassProblemID(request.POST)
        if form.is_valid():
            problem_id = form.cleaned_data["problem_id"]
            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                messages.error(request, "Unable to locate problem")
            user = request.user
            submissions = Submission.objects.filter(user=user, problem=problem).order_by("-date_submitted")
            return render(request, "problems/page/submission_window.html", {"submissions": submissions})

@login_required
def problem_testcase_window(request, problem_id):
    if request.method == "POST":
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            messages.error(request, "Unable to locate problem")
        example_testcases = ExampleTestcase.objects.filter(problem=problem)
        return render(request, "problems/page/testcase_window.html", {"testcases": example_testcases, "problem": problem})

@login_required
def problem_output_window(request, problem_id):
    try:
        problem = Problem.objects.get(id=problem_id)
    except Problem.DoesNotExist:
        messages.error(request, "Unable to locate problem")
    return render(request, "problems/page/output_window_placeholder.html", {"problem": problem})


@login_required
def filter_problem_categories(request):
    if request.method == "POST":
        form = FilterCategories(request.POST)
        if form.is_valid():
            category_id = form.cleaned_data["category_id"]
            user = request.user
            if category_id == "all":
                user_status_subquery = UserProblem.objects.filter(problem=OuterRef("pk"), user=user).values("status")[:1]
                problems = Problem.objects.annotate(user_status=Subquery(user_status_subquery))
                return render(request, "problems/list/filter_problem_categories.html", {"problems": problems})
            else:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    pass
                user_status_subquery = UserProblem.objects.filter(problem=OuterRef("pk"), user=user).values("status")[:1]
                problems = Problem.objects.filter(category=category).annotate(user_status=Subquery(user_status_subquery))
                return render(request, "problems/list/filter_problem_categories.html", {"problems": problems})


            

