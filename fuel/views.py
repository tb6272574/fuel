# Create your views here.
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib import auth
from fuel.models import FuelUser, Profile, Record, Amount
from fuel.settings import WEBSITE_NAME
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
import datetime

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
            #addloginbonus(request)
            auth.login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:
            return render_index(request, login_fail=True)

    else:
        return render_index(request, login_fail=True)

def addloginbonus(request):
    #try:
        #t=Amount.objects.filter(time.date==datetime.datetime.now()).filter(atype=2).get(user=request.user)
    #    t=Amount.objects.get(user=request.user)
    #except ObjectDoesNotExist:
    #    Profile(user=request.user).add_daily_bonus()

    #t=Profile(user=request.user);
    #t.add_daily_bonus()
    print 'nothing'

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
    return HttpResponse('ok')

# requires logged in
def home(request):
    t = loader.get_template('home.html')
    c = RequestContext(request, {'website_name': WEBSITE_NAME})
    return HttpResponse(t.render(c))  
#return HttpResponse('%s <a href="/logout/">logout</a>'%request.user.get_full_name())

# requires logged in; logs out
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('login'))

