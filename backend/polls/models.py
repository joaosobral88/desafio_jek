
from django.db import models


class Poll(models.Model):
    # Estados possíveis de uma votação
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        OPEN = "open", "Aberta"
        CLOSED = "closed", "Fechada"

    question = models.CharField(max_length=255)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class Option(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="options"
    )

    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class Vote(models.Model):
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="votes"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voto na opção {self.option_id}"
