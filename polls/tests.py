import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice

# Create your tests here.
class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)

def create_question(question_text, days):
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)

def create_choice(choice_text, question):
    return question.choice_set.create(choice_text=choice_text)

class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )
    
    def test_future_question(self):
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_two_past_questions(self):
        create_question(question_text="Past question 1.", days=-30)
        create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )

class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        past_question = create_question(question_text='Past question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

class VoteViewTests(TestCase):
    """
    Djangoチュートリアル5に追加
    投票の実行後の確認
    """

    def test_vote_post(self):
        """
        POST Only
        """

        # 新しい質問と回答を2つ準備
        past_question = create_question(question_text='Past question.', days=-1)
        past_choice_one = create_choice(choice_text='Choice 1', question=past_question)
        past_choice_two = create_choice(choice_text='Choice 2', question=past_question)

        url = reverse('polls:vote', args=(past_question.id,))

        # status_code=302が返ってくる
        response = self.client.post(url, {'choice' : past_choice_one.id})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('polls:results', args=(past_question.id,)),
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
        )

    def test_vote_post_redirect(self):
        """
        POST & Redirect
        """

        # 新しい質問と回答を2つ準備
        past_question = create_question(question_text='Past question.', days=-1)
        past_choice_one = create_choice(choice_text='Choice 1', question=past_question)
        past_choice_two = create_choice(choice_text='Choice 2', question=past_question)

        url = reverse('polls:vote', args=(past_question.id,))

        # 最終的なリダイレクト先のページ情報が返ってくる
        response = self.client.post(url, {'choice' : past_choice_one.id}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choice 1 -- 1 vote')
        self.assertContains(response, 'Choice 2 -- 0 vote')
        self.assertEqual(response.context['question'].question_text, 'Past question.')
        self.assertQuerysetEqual(
            response.context['question'].choice_set.all(),
            ['<Choice: Choice 1>', '<Choice: Choice 2>'],
            ordered=False
        )
