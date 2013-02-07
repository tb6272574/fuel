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
    c = RequestContext(request, {'website_name': WEBSITE_NAME,
    'scale_set': Scale.objects.all()})
    return HttpResponse(t.render(c))

def addscale(request, scaleid, amount):
   if not request.user.is_authenticated():
       return HttpResponseForbidden()
   amount = int(amount)
   scaleid = int(scaleid) 
   print 'scale id=' + str(scaleid) + ' amount=' + str(amount)
   scale = Scale.objects.get(id=scaleid)
   #check whether the user has enough amount
   fueluser = FuelUser.objects.get(id=request.user.id)
   t = loader.get_template('game.html')
   c = RequestContext(request, {'website_name': WEBSITE_NAME,'scale_set': Scale.objects.all()});
   print 'current_amount = '+str(fueluser.current_amount())
   if amount > fueluser.current_amount():
       c = RequestContext(request, {'website_name': WEBSITE_NAME,'scale_set': Scale.objects.all(), 'point_not_enough': True});
       print 'Not enough points'
   else:
      scale.add_amount(amount, request.user)
      if not scale.active:
          c = RequestContext(request, {'website_name': WEBSITE_NAME,'scale_set': Scale.objects.all(), 'win': True, 'money': scale.money});
          print 'he wins!'
   return HttpResponse(t.render(c))

# requires logged in; logs out
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('login'))

