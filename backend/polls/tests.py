import uuid

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from rest_framework.test import APITestCase

from .models import Option, Poll, Vote


class PollAPITests(APITestCase):
    def setUp(self):
        self.poll = Poll.objects.create(question="Qual é a melhor linguagem?")
        self.first = Option.objects.create(poll=self.poll, text="Python")
        self.second = Option.objects.create(poll=self.poll, text="C")
        self.token = str(uuid.uuid4())

    def open_poll(self):
        self.poll.status = Poll.Status.OPEN
        self.poll.save()

    def cast_vote(self, poll=None, option=None, token=None):
        return self.client.post(
            f"/api/public/polls/{(poll or self.poll).pk}/vote/",
            {"option_id": (option or self.first).pk, "token": token or self.token},
            format="json",
        )

    def test_create_poll_starts_as_draft_and_trims_text(self):
        response = self.client.post("/api/host/polls/", {
            "question": "  O que escolher?  ", "options": ["  Sim ", "Não"], "status": "open",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["question"], "O que escolher?")
        self.assertEqual(response.data["options"][0]["text"], "Sim")

    def test_create_accepts_two_to_five_options(self):
        for count in range(2, 6):
            with self.subTest(count=count):
                response = self.client.post("/api/host/polls/", {
                    "question": "Escolha", "options": [str(i) for i in range(count)],
                }, format="json")
                self.assertEqual(response.status_code, 201)
                self.assertEqual(len(response.data["options"]), count)

    def test_invalid_creation_is_rejected_without_saving(self):
        invalid = [
            {}, {"question": "", "options": ["A", "B"]},
            {"question": "   ", "options": ["A", "B"]},
            {"question": "X" * 256, "options": ["A", "B"]},
            {"question": 42, "options": ["A", "B"]},
            {"question": "Q", "options": []},
            {"question": "Q", "options": ["A"]},
            {"question": "Q", "options": list("ABCDEF")},
            {"question": "Q", "options": ["A", "a "]},
            {"question": "Q", "options": ["A", "   "]},
            {"question": "Q", "options": ["A", "X" * 256]},
            {"question": "Q", "options": ["A", None]},
            {"question": "Q", "options": ["A", 12]},
            {"question": "Q", "options": ["A", {}]},
            {"question": "Q", "options": "A,B"},
        ]
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.client.post("/api/host/polls/", payload, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.data)
        self.assertEqual(Poll.objects.count(), 1)
        self.assertEqual(Option.objects.count(), 2)

    def test_public_list_hides_drafts_and_vote_counts(self):
        opened = Poll.objects.create(question="Aberta", status="open")
        closed = Poll.objects.create(question="Fechada", status="closed")
        response = self.client.get("/api/public/polls/")
        self.assertEqual({poll["id"] for poll in response.data}, {opened.pk, closed.pk})
        self.assertNotIn("total", response.data[0])
        self.assertEqual(len(self.client.get("/api/host/polls/").data), 3)

    def test_state_follows_draft_open_closed_only(self):
        path = f"/api/host/polls/{self.poll.pk}/status/"
        for state, expected in [("closed", 400), ("open", 200), ("draft", 400),
                                ("open", 400), ("closed", 200), ("open", 400)]:
            with self.subTest(state=state):
                self.assertEqual(self.client.patch(path, {"status": state}, format="json").status_code, expected)
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.status, "closed")

    def test_invalid_status_is_rejected(self):
        response = self.client.patch(f"/api/host/polls/{self.poll.pk}/status/", {"status": "invalid"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_vote_is_recorded_with_confirmation(self):
        self.open_poll()
        response = self.cast_vote()
        self.assertEqual(response.status_code, 201)
        self.assertIn("registado", response.data["detail"])
        vote = Vote.objects.get()
        self.assertEqual(vote.poll_id, self.poll.pk)
        self.assertEqual(vote.option_id, self.first.pk)
        self.assertEqual(str(vote.token), self.token)

    def test_duplicate_token_cannot_vote_for_another_option(self):
        self.open_poll()
        self.assertEqual(self.cast_vote().status_code, 201)
        self.assertEqual(self.cast_vote(option=self.second).status_code, 409)
        self.assertEqual(self.cast_vote().status_code, 409)
        self.assertEqual(Vote.objects.count(), 1)

    def test_token_can_vote_in_different_polls(self):
        self.open_poll()
        other = Poll.objects.create(question="Outra?", status="open")
        option = Option.objects.create(poll=other, text="Sim")
        self.assertEqual(self.cast_vote().status_code, 201)
        self.assertEqual(self.cast_vote(poll=other, option=option).status_code, 201)

    def test_database_enforces_unique_poll_and_token(self):
        Vote.objects.create(poll=self.poll, option=self.first, token=self.token)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Vote.objects.create(poll=self.poll, option=self.second, token=self.token)

    def test_drafts_and_closed_polls_reject_votes(self):
        self.assertEqual(self.cast_vote().status_code, 404)
        self.poll.status = "closed"
        self.poll.save()
        self.assertEqual(self.cast_vote().status_code, 400)
        self.assertEqual(Vote.objects.count(), 0)

    def test_option_must_belong_to_poll(self):
        self.open_poll()
        other = Poll.objects.create(question="Outra?")
        option = Option.objects.create(poll=other, text="Outra opção")
        self.assertEqual(self.cast_vote(option=option).status_code, 400)
        self.assertEqual(Vote.objects.count(), 0)

    def test_invalid_vote_payloads(self):
        self.open_poll()
        for payload in [{}, {"option_id": self.first.pk},
                        {"option_id": self.first.pk, "token": "not-a-uuid"},
                        {"option_id": -1, "token": self.token},
                        {"option_id": 99999, "token": self.token}]:
            with self.subTest(payload=payload):
                response = self.client.post(f"/api/public/polls/{self.poll.pk}/vote/", payload, format="json")
                self.assertEqual(response.status_code, 400)
        self.assertEqual(Vote.objects.count(), 0)

    def test_public_results_only_after_closing(self):
        path = f"/api/public/polls/{self.poll.pk}/results/"
        self.assertEqual(self.client.get(path).status_code, 404)
        self.open_poll()
        self.assertEqual(self.client.get(path).status_code, 403)
        self.cast_vote()
        self.poll.status = "closed"
        self.poll.save()
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)

    def test_host_results_available_in_every_state_including_zero_votes(self):
        path = f"/api/host/polls/{self.poll.pk}/results/"
        for state in Poll.Status.values:
            self.poll.status = state
            self.poll.save()
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["total"], 0)
            self.assertEqual([item["percentage"] for item in response.data["options"]], [0, 0])

    def test_counts_and_percentages_refresh(self):
        self.open_poll()
        path = f"/api/host/polls/{self.poll.pk}/results/"
        self.assertEqual(self.client.get(path).data["total"], 0)
        self.cast_vote()
        self.cast_vote(token=str(uuid.uuid4()))
        self.cast_vote(option=self.second, token=str(uuid.uuid4()))
        results = self.client.get(path).data
        self.assertEqual(results["total"], 3)
        self.assertEqual([item["count"] for item in results["options"]], [2, 1])
        self.assertEqual([item["percentage"] for item in results["options"]], [66.7, 33.3])

    def test_unknown_polls_return_404(self):
        for path in ["public/polls/99999/results/", "host/polls/99999/results/"]:
            self.assertEqual(self.client.get(f"/api/{path}").status_code, 404)
        response = self.client.post("/api/public/polls/99999/vote/", {
            "option_id": self.first.pk, "token": self.token,
        }, format="json")
        self.assertEqual(response.status_code, 404)


class VoteMigrationTests(TransactionTestCase):
    def test_existing_votes_are_preserved_with_distinct_tokens(self):
        # Executa as duas versões do esquema apenas na base de dados de testes.
        executor = MigrationExecutor(connection)
        executor.migrate([("polls", "0001_initial")])
        try:
            apps = executor.loader.project_state([("polls", "0001_initial")]).apps
            old_poll = apps.get_model("polls", "Poll").objects.create(question="Antiga")
            old_option = apps.get_model("polls", "Option").objects.create(poll=old_poll, text="Sim")
            old_vote = apps.get_model("polls", "Vote")
            old_vote.objects.create(option=old_option)
            old_vote.objects.create(option=old_option)
        finally:
            MigrationExecutor(connection).migrate([("polls", "0002_vote_token")])
        votes = list(Vote.objects.filter(poll_id=old_poll.pk))
        self.assertEqual(len(votes), 2)
        self.assertNotEqual(votes[0].token, votes[1].token)
        self.assertTrue(all(vote.option_id == old_option.pk for vote in votes))
