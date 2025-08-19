from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, post_delete


# -----------------------
# Category (oddiy klass)
# -----------------------
class Category(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


# -----------------------
# Test (asosiy test modeli)
# -----------------------
class Test(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    maximum_attemps = models.PositiveBigIntegerField()
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(
        default=(timezone.now() + timezone.timedelta(days=10))
    )
    pass_percentage = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# -----------------------
# Question (test savollari)
# -----------------------
class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question = models.CharField(max_length=300)
    a = models.CharField(max_length=150)
    b = models.CharField(max_length=150)
    c = models.CharField(max_length=150)
    d = models.CharField(max_length=150)
    true_answer = models.CharField(max_length=150, help_text="E.x: a")

    def __str__(self):
        return self.question


# -----------------------
# CheckTest (foydalanuvchi test topshirgan natijasi)
# -----------------------
class CheckTest(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    finded_question = models.PositiveBigIntegerField(default=0)   # to‘g‘ri topilgan savollar
    user_passed = models.BooleanField(default=False)              # testdan o‘tdimi?
    percentage = models.PositiveBigIntegerField(default=0)        # foiz
    taken_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Test of {self.student.username}"


# -----------------------
# CheckQuestion (foydalanuvchi bergan javoblar)
# -----------------------
class CheckQuestion(models.Model):
    checktest = models.ForeignKey(CheckTest, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    given_answer = models.CharField(max_length=1, help_text="E.x: a")
    true_answer = models.CharField(max_length=1, help_text="E.x: a")
    is_true = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer of {self.checktest.student.username} for {self.question}"


# -----------------------
# Signals
# -----------------------

# Har bir CheckQuestion saqlanayotganda: javob to‘g‘riligini belgilash
@receiver(pre_save, sender=CheckQuestion)
def check_answer(sender, instance, **kwargs):
    if instance.given_answer == instance.true_answer:
        instance.is_true = True
    else:
        instance.is_true = False


#  Har bir CheckQuestion qo‘shilganda/o‘chirilib/yangi saqlanganda:
#  tegishli CheckTest avtomatik yangilanadi
@receiver([post_save, post_delete], sender=CheckQuestion)
def update_checktest_results(sender, instance, **kwargs):
    checktest = instance.checktest
    correct_count = CheckQuestion.objects.filter(
        checktest=checktest, is_true=True
    ).count()
    total = CheckQuestion.objects.filter(checktest=checktest).count()
    checktest.finded_question = correct_count
    checktest.percentage = (correct_count * 100 // total) if total > 0 else 0
    checktest.user_passed = checktest.percentage >= checktest.test.pass_percentage

    checktest.save(update_fields=["finded_question", "percentage", "user_passed"])
