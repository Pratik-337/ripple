
print('testing error logging...')
try:
    from app.models.change import *
except Exception as e:
    import traceback
    with open('model_error_log.txt', 'w') as f:
        traceback.print_exc(file=f)

