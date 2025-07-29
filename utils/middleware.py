from django.conf import settings
from freezegun import freeze_time
from datetime import datetime

class FreezeTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.default_freeze_time = getattr(settings, 'FREEZE_TIME', None)

    def __call__(self, request):
        freeze_param = request.GET.get('freeze')
        freeze_dt = None

        if freeze_param:
            try:
                freeze_dt = datetime.strptime(freeze_param, '%Y-%m-%d')
            except ValueError:
                try:
                    freeze_dt = datetime.strptime(freeze_param, '%Y-%m-%d %H:%M')
                except ValueError:
                    pass

        freeze_value = freeze_dt or self.default_freeze_time

        if freeze_value:
            print(f"[FreezeTimeMiddleware] Using frozen time: {freeze_value}")
            with freeze_time(freeze_value):
                return self.get_response(request)

        print("[FreezeTimeMiddleware] No frozen time applied.")
        return self.get_response(request)