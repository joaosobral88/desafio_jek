
from django.db import models

#define um metodo para guardar votacoes
class Poll(models.Model):
    # Estados possíveis de uma votação
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        OPEN = "open", "Aberta"
        CLOSED = "closed", "Fechada"
#guarda a pergunta, escrevemos assim porque uma variável Python normal não chega para descrever ao Django como guardar essa informação na base de dados.
    question = models.CharField(max_length=255)

    status = models.CharField(
        max_length=10,
        #dizer ao django quais sao os status que estamos a aceitar
        choices=Status.choices,
        #padrao/assumido (por exemplo quando nao dizemos o estado)
        default=Status.DRAFT
    )
#guardar data e hora a que foi criada util para ordenar por exemplo
    created_at = models.DateTimeField(auto_now_add=True)
#define como um objeto deve ser representado quando o convertemos em texto
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
