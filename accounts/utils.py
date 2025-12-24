def is_trainer(user):
    return user.groups.filter(name='Trainer').exists()

def is_admin(user):
    return user.is_superuser or user.groups.filter(
        name__in=[
            'Admin',
            'Project Manager',
            'Monitoring Manager',
            'Supervisor'
        ]
    ).exists()
