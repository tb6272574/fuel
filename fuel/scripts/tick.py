from fuel.models import *

def run():
    for u in FuelUser.objects.all():
        u.status_tick()
    print "ticked!"
