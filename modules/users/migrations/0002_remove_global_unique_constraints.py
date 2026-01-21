# Generated migration to remove global unique constraints on username and email

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        # Remove the global unique constraint on username field
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                max_length=150,
                verbose_name="username",
                help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                validators=[],  # Validators will be inherited from model
            ),
        ),
        # Remove the global unique constraint on email field (if exists)
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                max_length=254,
                verbose_name="email address",
                blank=True,
            ),
        ),
    ]
