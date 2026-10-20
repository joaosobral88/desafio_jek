from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Poll, Vote
from .serializers import CreatePollSerializer, PollSerializer, StatusSerializer, VoteSerializer

#devolve votacoes para o publico poder ver
def public_polls():
    return Poll.objects.exclude(status=Poll.Status.DRAFT)

#vai buscar todas as votacoes com uma so consulta
@api_view(["GET", "POST"])
def host_polls(request):
    if request.method == "GET":
        polls = Poll.objects.prefetch_related("options").order_by("-created_at")
        return Response(PollSerializer(polls, many=True).data)
    serializer = CreatePollSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(PollSerializer(serializer.save()).data, status=201)

#nao inclui rascunhos
@api_view(["GET"])
def public_poll_list(request):
    polls = public_polls().prefetch_related("options").order_by("-created_at")
    return Response(PollSerializer(polls, many=True).data)


@api_view(["PATCH"])
def change_status(request, poll_id):
    #valida que tem um status
    serializer = StatusSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    new_status = serializer.validated_data["status"]
    #vai buscar a votacao, se nao existir da 404
    poll = get_object_or_404(Poll, pk=poll_id)
    #tabela das transicoes permitidas
    next_status = {Poll.Status.DRAFT: Poll.Status.OPEN, Poll.Status.OPEN: Poll.Status.CLOSED}
    if next_status.get(poll.status) != new_status:
        return Response({"detail": "Só pode abrir um rascunho ou fechar uma votação aberta."}, status=400)
    changed = Poll.objects.filter(pk=poll.pk, status=poll.status).update(status=new_status)
    if not changed:
        return Response({"detail": "O estado mudou. Atualize a lista e tente novamente."}, status=409)
    poll.refresh_from_db()
    return Response(PollSerializer(poll).data)

#registar o voto de um participante
@api_view(["POST"])
def vote(request, poll_id):
    serializer = VoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        with transaction.atomic():
            # Em SQLite esta escrita bloqueia outras escritas até ao fim da transação.
            # Impede que o anfitrião feche a votação entre a verificação e o voto.
            opened = Poll.objects.filter(pk=poll_id, status=Poll.Status.OPEN).update(status=Poll.Status.OPEN)
            if not opened:
                get_object_or_404(public_polls(), pk=poll_id)
                return Response({"detail": "Esta votação já não está aberta."}, status=400)
            poll = Poll.objects.get(pk=poll_id)
            option = poll.options.filter(pk=serializer.validated_data["option_id"]).first()
            if option is None:
                return Response({"detail": "Escolha uma opção válida desta votação."}, status=400)
            Vote.objects.create(poll=poll, option=option, token=serializer.validated_data["token"])
    except IntegrityError:
        return Response({"detail": "Já votou nesta votação com este navegador."}, status=409)
    return Response({"detail": "O seu voto foi registado. Obrigado por participar!"}, status=201)

#mostrar os resultados ao publico
def poll_results(poll):
    options = list(poll.options.annotate(count=Count("votes")).order_by("id"))
    total = sum(option.count for option in options)
    return {
        "poll_id": poll.pk, "total": total,
        "options": [
            {"id": option.pk, "text": option.text, "count": option.count,
             "percentage": round(option.count * 100 / total, 1) if total else 0}
            for option in options
        ],
    }
#mostrar os resultados ao anfitriao
@api_view(["GET"])
def host_results(request, poll_id):
    return Response(poll_results(get_object_or_404(Poll, pk=poll_id)))


@api_view(["GET"])
def public_results(request, poll_id):
    poll = get_object_or_404(public_polls(), pk=poll_id)
    if poll.status != Poll.Status.CLOSED:
        return Response({"detail": "Os resultados ficam disponíveis quando a votação fechar."}, status=403)
    return Response(poll_results(poll))
