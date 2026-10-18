from django.db import transaction
from rest_framework import serializers
from .models import Option, Poll


class TextField(serializers.CharField):
    # Rejeita números/objetos em vez de os converter silenciosamente em texto.
    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError("Introduza texto válido.")
        return super().to_internal_value(data)


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text"]


class PollSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = ["id", "question", "status", "created_at", "options"]


class CreatePollSerializer(serializers.Serializer):
    question = TextField(max_length=255, allow_blank=False)
    options = serializers.ListField(
        child=TextField(max_length=255, allow_blank=False),
        min_length=2, max_length=5,
    )

    def validate_options(self, options):
        # Os campos de texto já removeram os espaços no início e no fim.
        normalized = [text.casefold() for text in options]
        if len(set(normalized)) != len(normalized):
            raise serializers.ValidationError("As opções não podem estar repetidas.")
        return options

    @transaction.atomic
    def create(self, validated_data):
        options = validated_data.pop("options")
        poll = Poll.objects.create(**validated_data)
        for text in options:
            Option.objects.create(poll=poll, text=text)
        return poll


class VoteSerializer(serializers.Serializer):
    option_id = serializers.IntegerField(min_value=1)
    token = serializers.UUIDField()


class StatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Poll.Status.choices)
