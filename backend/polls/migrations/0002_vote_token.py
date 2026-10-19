import uuid
from django.db import migrations, models
import django.db.models.deletion


def preserve_votes(apps, schema_editor):
    Vote = apps.get_model("polls", "Vote")
    for vote in Vote.objects.select_related("option").all():
        vote.poll_id = vote.option.poll_id
        vote.token = uuid.uuid4()
        vote.save(update_fields=["poll", "token"])


class Migration(migrations.Migration):
    dependencies = [("polls", "0001_initial")]
    operations = [
        #as colunas novas comecam vazias
        migrations.AddField(model_name="vote", name="poll", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="polls.poll")),
        migrations.AddField(model_name="vote", name="token", field=models.UUIDField(null=True)),
        #percorre votos e preenche poll
        migrations.RunPython(preserve_votes, migrations.RunPython.noop),
       #torna as colunas obrigatorias
        migrations.AlterField(model_name="vote", name="poll", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="polls.poll")),
        migrations.AlterField(model_name="vote", name="token", field=models.UUIDField(default=uuid.uuid4)),
        #regra da unicidade
        migrations.AddConstraint(model_name="vote", constraint=models.UniqueConstraint(fields=("poll", "token"), name="unique_vote_per_poll_token")),
    ]
