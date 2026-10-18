from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="Poll", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("question", models.CharField(max_length=255)),
            ("status", models.CharField(choices=[("draft", "Rascunho"), ("open", "Aberta"), ("closed", "Fechada")], default="draft", max_length=10)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name="Option", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("text", models.CharField(max_length=255)),
            ("poll", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="polls.poll")),
        ]),
        migrations.CreateModel(name="Vote", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("option", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="polls.option")),
        ]),
    ]
