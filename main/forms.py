from django import forms
from .models import Test, Question

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('title', 'category', 'maximum_attemps', 'start_date', 'end_date', 'pass_percentage')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'category': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'maximum_attemps': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'pass_percentage': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
        }

    def save(self, request, commit=True):
        test = self.instance
        test.author = request.user
        super().save(commit)
        return test.id


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question', 'a', 'b', 'c', 'd', 'true_answer')
        widgets = {
            'question': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'a': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'b': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'c': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'd': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'true_answer': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
        }

    def save(self, test_id, commit=True):
        question = self.instance
        question.test = Test.objects.get(id=test_id)
        super().save(commit)
        return question
