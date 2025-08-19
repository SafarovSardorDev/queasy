# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from django.utils import timezone
from .models import Test, Question, CheckQuestion, CheckTest
from reportlab.lib.colors import Color, black, lightgrey, white
from reportlab.platypus import Table, TableStyle
from .forms import TestForm, QuestionForm
from django.contrib.auth.models import User

# -----------------------
# Foydalanuvchi ro‘yxatdan o‘tishi
# -----------------------
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


# -----------------------
# Bosh sahifa (testlar ro‘yxati)
# -----------------------
def index(request):
    tests = Test.objects.order_by("-id")
    return render(request, "index.html", {"tests": tests})

# -----------------------
# Profile
# -----------------------
@login_required(login_url="login")
def profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)

    # Teskari tartibda yaratgan testlar
    created_tests = profile_user.test_set.all().order_by("-start_date")

    # Teskari tartibda ishlagan testlar
    solved_tests = profile_user.checktest_set.all().order_by("-taken_at")

    context = {
        "profile_user": profile_user,
        "is_owner": request.user == profile_user,
        "created_tests": created_tests,
        "solved_tests": solved_tests,
    }
    return render(request, "profile.html", context)



# -----------------------
# Test boshlashdan oldingi sahifa
# -----------------------
@login_required(login_url="login")
def ready_to_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    return render(request, "ready_to_test.html", {"test": test})


# -----------------------
# Testni PDF formatda yuklab olish
# -----------------------

def add_watermark(p, width, height):
    watermark_text = "QUEASY"
    p.saveState()
    p.setFont("Helvetica-Bold", 40)
    p.setFillColor(Color(0.8, 0.8, 0.8, alpha=0.3))
    p.translate(width / 2, height / 2)
    p.rotate(45)
    p.drawCentredString(0, 0, watermark_text)
    p.restoreState()


@login_required(login_url="login")
def download_test_pdf(request, test_id):
    test = get_object_or_404(Test, id=test_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{test.title}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # --- Title page ---
    add_watermark(p, width, height)
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - inch, test.title)

    y = height - (1.5 * inch)
    p.setFont("Helvetica", 12)

    # To‘g‘ri javoblar uchun list
    question_numbers = []
    correct_answers = []

    # --- Questions & options ---
    for i, q in enumerate(test.question_set.all(), start=1):
        p.drawString(inch, y, f"{i}. {q.question}")
        y -= 15
        p.drawString(inch + 20, y, f"A) {q.a}")
        y -= 15
        p.drawString(inch + 20, y, f"B) {q.b}")
        y -= 15
        p.drawString(inch + 20, y, f"C) {q.c}")
        y -= 15
        p.drawString(inch + 20, y, f"D) {q.d}")
        y -= 25

        question_numbers.append(str(i))
        correct_answers.append(q.true_answer.upper())

        if y < inch:
            p.showPage()
            add_watermark(p, width, height)
            y = height - inch
            p.setFont("Helvetica", 12)

    # --- Correct answers table ---
    p.showPage()
    add_watermark(p, width, height)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - inch, "Correct Answers")

    # Jadval ma'lumotlari
    table_data = [ ["Questions"] + question_numbers,
                   ["Correct Answers"] + correct_answers ]

    table = Table(table_data, colWidths=None)  # avtomatik kenglik
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), lightgrey),
        ("TEXTCOLOR", (0,0), (-1,0), black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (-1,1), "Helvetica"),
        ("GRID", (0,0), (-1,-1), 0.5, black),
        ("BACKGROUND", (0,1), (-1,1), white),
    ]))

    # Jadvalni sahifaga joylash
    table_width, table_height = table.wrap(0,0)
    table.drawOn(p, inch, height - (2*inch) - table_height)

    p.save()
    return response



# -----------------------
# Test topshirish sahifasi
# -----------------------
@login_required(login_url="login")
def test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    attemps = CheckTest.objects.filter(student=request.user, test=test).count()
    
    if (timezone.now()>=test.start_date and timezone.now()<=test.end_date) and attemps<test.maximum_attemps:
        questions = Question.objects.filter(test=test)
        if request.method == "POST":
            checktest = CheckTest.objects.create(student=request.user, test=test)
            for question in questions:
                given_answer = request.POST.get(str(question.id))
                CheckQuestion.objects.create(
                    checktest=checktest,
                    question=question,
                    given_answer=given_answer,
                    true_answer=question.true_answer,
                )
            messages.success(request, "Test completed! Your result has been calculated.")
            return redirect("checktest", checktest.id) 

        return render(request, "test.html", {"test": test, "questions": questions})
    else:
        return render(request, "error.html", {
            "message": "This test has either expired or you have reached the maximum number of attempts."
        })
    
@login_required(login_url="login")
def checktest(request, checktest_id):
    checktest=get_object_or_404(CheckTest, id=checktest_id, student=request.user)
    return render(request, 'checktest.html', {'checktest':checktest})


@login_required(login_url="login")
def new_test(request):
    form = TestForm()
    if request.method == "POST":
        form = TestForm(data=request.POST)
        if form.is_valid():
            test_id = form.save(request)
            return redirect('new_question', test_id)
    return render(request, 'new_test.html', {'form': form})


@login_required(login_url="login")
def new_question(request, test_id):
    test = get_object_or_404(Test, id=test_id)

    if test.author != request.user:
        return HttpResponse("Something Went Wrong!!!")

    form = QuestionForm()

    if request.method == "POST":
        form = QuestionForm(data=request.POST)
        if form.is_valid():
            form.save(test_id)

            # Tugmalarni tekshirish
            if "save_and_finish" in request.POST:
                return redirect('index')  # Tugallab index sahifaga qaytadi
            else:
                return redirect("new_question", test_id)

    return render(request, 'new_question.html', {'form': form, 'test': test})


