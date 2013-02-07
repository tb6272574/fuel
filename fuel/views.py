# Create your views here.
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib import auth
from fuel.models import FuelUser, Profile, Record, Amount, Scale
from fuel.settings import WEBSITE_NAME
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
import datetime, pytz
import math

GAME_NOT_ENOUGH_POINTS = 'not_enough_points'
GAME_ALREADY_FINISHED = 'already_finished'
GAME_WON = 'won'
GAME_MONEY = 'money'
GAME_SPEND = 'spend'

def index(request):
    if request.user.is_anonymous():
        return HttpResponseRedirect(reverse('login'))
    else:
        return HttpResponseRedirect(reverse('home'))

def render_index(request, login_fail=False):
    t = loader.get_template('index.html')
    c = RequestContext(request, {'login_fail': login_fail, 'website_name': WEBSITE_NAME})
    if 'email' in request.POST:
        c.update({'email': request.POST['email']})
    return HttpResponse(t.render(c))

# requires not logged in
def login(request):

    if not request.user.is_anonymous():
        return HttpResponseRedirect(reverse('home'))

    if request.method == 'GET':
        return render_index(request)

    elif 'email' in request.POST and 'password' in request.POST:

        user = auth.authenticate(username=request.POST['email'], password=request.POST['password'])

        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:
            return render_index(request, login_fail=True)

    else:
        return render_index(request, login_fail=True)

#add record
def addrecord(request):
    #print request.GET['calories']
    #t = loader.get_template('home.html')
    #if (not request.GET['step'].isdigit()):
    #    print 'bad step'
    #    c = RequestContext(request, {'website_name': WEBSITE_NAME, 'submit_fail': True, 'submit_fail_msg': 'Step should be a non-negative integer'})
    #    return HttpResponse(t.render(c))
    #if (not request.GET['calories'].isdigit()):              
    #    c = RequestContext(request, {'website_name': WEBSITE_NAME, 'submit_fail': True, 'submit_fail_msg': 'Calories should be a non-negative integer'})
    #    return HttpResponse(t.render(c))
    #if (not request.GET['fuel_score'].isdigit()):          
    #    c = RequestContext(request, {'website_name': WEBSITE_NAME, 'submit_fail': True, 'submit_fail_msg': 'fuel_score should be a non-negative integer'})
    #    return HttpResponse(t.render(c))
    year, month, day = request.GET['date'].split('-')
    #if ((not year.isdigit()) or (not month.isdigit()) or (not day.isdigit())):
    #    c = RequestContext(request, {'website_name': WEBSITE_NAME, 'submit_fail': True, 'submit_fail_msg': 'Date format not right'})
    #    return HttpResponse(t.render(c))
    try:
        t=Record.objects.filter(date=datetime.date(int(year),int(month),int(day))).get(user=request.user)
        t.amount.delete()
        t.delete()
    except ObjectDoesNotExist:
        print 'No clash'
    t = Record(user=request.user)
    t.date = datetime.date(int(year), int(month), int(day))
    # the following three all need to be ints not strings
    t.steps = int(request.GET['step'])
    t.calories = int(request.GET['calories'])
    t.fuelscore = int(request.GET['fuel_score'])
    # then this will work
    t.save_amount()
    request.user.get_profile().get_fueluser().add_status_fuelscore(t.fuelscore)

    tz=pytz.timezone('America/Los_Angeles')
    today = datetime.datetime.now()
    #today = tz.localize(today)
    today = today.date()
    for t in Amount.objects.all():#.filter(atype=2).filter(user=request.user):
        print t.time.astimezone(tz)
        print today
        if (t.time.astimezone(tz).date() == today) and (t.atype==2) and (t.user == request.user):
            return HttpResponse('ok')
    FuelUser.objects.get(id=request.user.id).add_daily_bonus()
    return HttpResponse('ok')

# requires logged in
def home(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    t = loader.get_template('home.html')
    c = RequestContext(request, {'website_name': WEBSITE_NAME})

    return HttpResponse(t.render(c))  

def stats(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    fuelscore = '{name:\"FuelScore\", values:['
    steps = '{name:\"Steps\", values:[' 
    calories = '{name:\"Calories\", values:[' 
    points = '{name:\"Points\", values:[' 
    for t in request.user.record_set.all():
        fuelscore = fuelscore + str(t.fuelscore) + ','
        steps = steps + str(t.steps) + ','
        calories = calories + str(t.calories) + ','
        points = points + str(t.get_amount()) + ','
    fuelscore = fuelscore + ']},'
    steps = steps + ']},'
    calories = calories + ']},'
    points = points + ']},'
    userdata = '[' + fuelscore + steps + calories + points + ']'
    print userdata
    t = loader.get_template('stats.html')
    c = RequestContext(request, {'website_name': WEBSITE_NAME, 'userdata': userdata})
    return HttpResponse(t.render(c))

# requires logged in
def game(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    
    t = loader.get_template('game.html')
    s_active = Scale.objects.filter(active=True)
    s_finished = sorted(Scale.objects.filter(active=False), key=lambda scale: scale.get_end_time(), reverse=True)

    c = RequestContext(request, {'website_name': WEBSITE_NAME, 'active_scales': s_active, 'finished_scales': s_finished})
    
    cookies_to_delete = []
    
    if GAME_ALREADY_FINISHED in request.COOKIES:
        c.update({GAME_ALREADY_FINISHED: True})
        cookies_to_delete.append(GAME_ALREADY_FINISHED)

    if GAME_NOT_ENOUGH_POINTS in request.COOKIES:
        c.update({GAME_NOT_ENOUGH_POINTS: True})
        cookies_to_delete.append(GAME_NOT_ENOUGH_POINTS)

    if GAME_WON in request.COOKIES:
        c.update({GAME_WON: True, GAME_MONEY: float(request.COOKIES[GAME_MONEY])})
        cookies_to_delete.append(GAME_WON)
        cookies_to_delete.append(GAME_MONEY)

    if GAME_SPEND in request.COOKIES:
        c.update({GAME_SPEND: int(request.COOKIES[GAME_SPEND])})
        cookies_to_delete.append(GAME_SPEND)

    response = HttpResponse(t.render(c))
    [response.delete_cookie(x) for x in cookies_to_delete]
    return response

def addscale(request, scaleid, amount):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    
    amount = int(amount)
    scaleid = int(scaleid) 
    print 'scale id=' + str(scaleid) + ' amount=' + str(amount)
    scale = Scale.objects.get(id=scaleid)

    #check whether the user has enough amount
    fueluser = FuelUser.objects.get(id=request.user.id)

    print 'current_amount = '+str(fueluser.current_amount())

    response = HttpResponseRedirect(reverse('game'))

    if amount > fueluser.current_amount():
        response.set_cookie(key=GAME_NOT_ENOUGH_POINTS, value=True, max_age=60)
    elif not scale.active:
        response.set_cookie(key=GAME_ALREADY_FINISHED, value=True, max_age=60)
    else:
        spent_amount = scale.add_amount(amount, request.user)
        if not scale.active:
            response.set_cookie(key=GAME_WON, value=True, max_age=60)
            response.set_cookie(key=GAME_MONEY, value=scale.money, max_age=60)
        response.set_cookie(key=GAME_SPEND, value=spent_amount, max_age=60)

    return response

# requires logged in; logs out
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('login'))

def faq(request):
    t = loader.get_template('faq.html')
    c = RequestContext(request, {'website_name': WEBSITE_NAME})
    return HttpResponse(t.render(c))

def history(request):
    t = loader.get_template('history.html')
    c = RequestContext(request, {'website_name': WEBSITE_NAME})
    # page the activities
    aset = request.user.amount_set.all()
    chunk_size = 10
    c.update({
        'amounts_paged': [aset[i*chunk_size:(i+1)*chunk_size] for i in range(int(math.ceil(len(aset)/float(chunk_size))))]
        })
    return HttpResponse(t.render(c))

def settings(request):
    t = loader.get_template('settings.html')
    c = RequestContext(request, {'website_name': WEBSITE_NAME})
    if request.method == 'GET':
        return HttpResponse(t.render(c))
    
    # change password
    action = request.POST['action']
    if action == 'update_password':
        old_pw = request.POST['old_pw']
        new_pw = request.POST['new_pw']
        new_pw_conf = request.POST['new_pw_conf']

        # verify that old_pw is correct
        u = authenticate(username=request.user.username, password=old_pw)

        # can't auth
        if u is None:
            c.update({'error_old_pw': True})

        # new_pw doesn't match new_pw_conf
        if new_pw != new_pw_conf:
            c.update({'error_mismatch': True})

        # can't be blank
        if len(new_pw) < 6:
            c.update({'error_too_short': True})

        # set as new password
        request.user.set_password(new_pw)
        request.user.save()
        c.update({'pw_success': True})

    return HttpResponse(t.render(c))

        
