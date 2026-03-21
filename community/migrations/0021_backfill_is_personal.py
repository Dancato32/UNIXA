from django.db import migrations


def backfill_is_personal(apps, schema_editor):
    """
    Mark existing auto-created personal workspaces as is_personal=True.
    These were created by the signals.py _create_personal_workspace handler
    and are identifiable by their name and being private + owned (no other members).
    """
    GroupWorkspace = apps.get_model('community', 'GroupWorkspace')
    WorkspaceMember = apps.get_model('community', 'WorkspaceMember')

    # Fix personal workspaces (named 'My Personal Workspace', private, owner is only member)
    personal_qs = GroupWorkspace.objects.filter(
        name='My Personal Workspace',
        privacy='private',
        workspace_type='general',
        is_personal=False,
    )
    for ws in personal_qs:
        member_count = WorkspaceMember.objects.filter(workspace=ws).count()
        if member_count <= 1:
            ws.is_personal = True
            ws.save(update_fields=['is_personal'])

    # Fix Nexa workspaces (named 'My Nexa Workspace', private, nexa type)
    nexa_qs = GroupWorkspace.objects.filter(
        name='My Nexa Workspace',
        privacy='private',
        workspace_type='nexa',
        is_personal=False,
    )
    for ws in nexa_qs:
        member_count = WorkspaceMember.objects.filter(workspace=ws).count()
        if member_count <= 1:
            ws.is_personal = True
            ws.save(update_fields=['is_personal'])


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0020_add_nexa_workspace_type'),
    ]

    operations = [
        migrations.RunPython(backfill_is_personal, migrations.RunPython.noop),
    ]
