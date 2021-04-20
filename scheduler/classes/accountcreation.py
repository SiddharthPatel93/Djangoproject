from scheduler_app.models import Account

def create_account(email, name, role):
    errors = []
    try:
        a = Account.objects.get(email=email) #user already exists in the database
        errors.append("User already exists")
        alert(errors)
    except:
        b = Account.objects.create(email=email, name=name, role=role, password=)
        
