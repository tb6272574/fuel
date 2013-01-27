# Create your views here.
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib import auth
from fuel.models import FuelUser, Profile, Record
from fuel.settings import WEBSITE_NAME
from django.core.urlresolvers import reverse

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
    t = Record(user=request.user)

    # you need to do something like
    #t.date = datetime.date(2013,1,27)
    t.date = request.GET['date']

    # the following three all need to be ints not strings
    t.steps = request.GET['step']
    t.calories = request.GET['calories']
    t.fuelscore = request.GET['fuel_score']

    # then this will work
    t.save_amount()

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
    
