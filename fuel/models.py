from django.db import models
from django.contrib.auth.models import User
import datetime, pytz, re, json
from math import ceil
from random import randint

# constants

DAILY_BONUS = {
        'b': 10,
        's': 30,
        'g': 50
        }

POINT_LIMITS = [2000, 1000, 1e6]
POINT_VALUES = [100, 50, 25]

POINT_MONEY = 0.005

STATUS_TICK_MINUTES = 3
STATUS_TICK_FREQUENCY = 1440/STATUS_TICK_MINUTES
STATUS_DEDUCTIONS_PER_DAY = {
        'b': 2200.0,
        's': 2600.0,
        'g': 3000.0
        }
STATUS_DEDUCTIONS_PER_TICK = {
        'b': STATUS_DEDUCTIONS_PER_DAY['b']/STATUS_TICK_FREQUENCY,
        's': STATUS_DEDUCTIONS_PER_DAY['s']/STATUS_TICK_FREQUENCY,
        'g': STATUS_DEDUCTIONS_PER_DAY['g']/STATUS_TICK_FREQUENCY,
        }
STATUS_LIMITS = {
        'b': 0,
        's': 2000,
        'g': 3000,
        'cap': 5000
        }

STATUS_LOG_FILE = '/opt/fuel/fuel/status-log'

SCALE_MONEY_LIMIT = {
        'low': 2.0,
        'high': 20.0,
        }

TYPES = (
        (0, 'reserved'),
        (1, 'Fuel band'),
        (2, 'Daily bonus'),
        (3, 'Game'),
        )

BOOST_DAYS = {
            'M': 'Monday',
            'T': 'Tuesday',
            'W': 'Wednesday',
            'H': 'Thursday',
            'F': 'Friday',
            'S': 'Saturday',
            'U': 'Sunday',
            }


STATUS = {
            'b': 'bronze',
            's': 'silver',
            'g': 'gold',
            }


# Create your models here.

class FuelUser(User):

    def name(self):
        return self.get_full_name()

    def image_url(self):
        return "%s-%s.jpg" % (
                re.sub('[^a-z]+','',self.last_name.lower()),
                self.first_name[0].lower()
                )

    def start_date(self):
        return self.profile.start_date.strftime('%m/%d/%y %H:%M:%S')

    def boost_day(self):
        return BOOST_DAYS[self.profile.boost_day]

    def status(self):
        return STATUS[self.profile.status]

    def current_amount(self):
        return sum([a.amount for a in self.amount_set.all()])  

    def winnings(self):
        return sum([s.money for s in Scale.objects.filter(active=False, winner=self)])

    def friends(self):
        try:
            n = self.friendnode
        except:
            print "not associated with node"
            return None

        return [x.user for x in n.friends.all() if x.user is not None]

    def add_daily_bonus(self):
        a = Amount()
        a.user = self
        a.amount = DAILY_BONUS[self.get_profile().status]
        a.atype = 2
        tz=pytz.timezone('America/Los_Angeles')
        a.action = 'Daily bonus for %s' % tz.localize(datetime.datetime.now()).astimezone(tz).strftime('%m/%d/%y')
        a.time = pytz.utc.localize(datetime.datetime.utcnow())
        a.save()

        return a.amount

    def current_amount(self):     
        return sum([a.amount for a in Amount.objects.filter(user=self)])

    def total_fuelscore(self):
        return sum([r.fuelscore for r in Record.objects.filter(user=self)])

    def status_tick(self):
        p = self.get_profile()
        nv = p.status_value - STATUS_DEDUCTIONS_PER_TICK[p.status]
        if nv < 0:
            nv = 0

#        with open(STATUS_LOG_FILE, 'a') as f:
#            f.write('[%s] %s: TICK %s, %.2f - %.2f = %.2f\n' %
#                    (
#                        datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'),
#                        self.email,
#                        STATUS[p.status],
#                        p.status_value,
#                        STATUS_DEDUCTIONS_PER_TICK[p.status],
#                        nv
#                        )
#                    )
        p.status_value = nv
        p.save()
        self.update_status()

    def update_status(self):
        status = 'b'
        p = self.get_profile()
        old_status = p.status
        for s in ['b', 's', 'g']:
            if p.status_value >= STATUS_LIMITS[s]:
                status = s
        
        if status != p.status:
#            with open(STATUS_LOG_FILE, 'a') as f:
#                f.write('[%s] %s: STAT %s -> %s\n' %
#                        (
#                            datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'),
#                            self.email,
#                            STATUS[p.status],
#                            STATUS[status],
#                            )
#                        )
            p.status = status
            p.save()
        return (old_status, status)

    def add_status_fuelscore(self, fuelscore):
        p = self.get_profile()
        ov = p.status_value
        nv = p.status_value + fuelscore
        if nv > STATUS_LIMITS['cap']:
            nv = STATUS_LIMITS['cap']

#        with open(STATUS_LOG_FILE, 'a') as f:
#            f.write('[%s] %s: FUEL %.2f + %d = %.2f\n' %
#                    (
#                        datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'),
#                        self.email,
#                        ov,
#                        fuelscore,
#                        nv
#                        )
#                    )

        p.status_value = nv
        p.save()
        old_status, new_status = self.update_status()

        return nv-ov

    def status_badge(self):
        badge_class = {
                'b': 'warning',
                's': 'default',
                'g': 'gold',
                }
        badge_name = {
                'b': 'Bronze',
                's': 'Silver',
                'g': 'Gold'
                }
        return "<span class=\"badge badge-%s\">%s</span>" % (badge_class[self.get_profile().status], badge_name[self.get_profile().status])

    def status_drain(self):
        return STATUS_DEDUCTIONS_PER_DAY[self.get_profile().status]

    def project(self):
        return self.project_set[0]
    class Meta:
        ordering = ['id']
        proxy = True

class Amount(models.Model):
    user = models.ForeignKey(User)
    scale = models.ForeignKey('Scale', blank=True, null=True)
    time = models.DateTimeField('Time', default='')
    amount = models.IntegerField('Amount', default=0)
    atype = models.IntegerField('Type', choices=TYPES, default=0)
    action = models.CharField('Action', max_length=100)
    
    def __unicode__(self):
        return u"#%d (%d)" % (self.id, self.amount)
    
    def get_date(self):
        tz=pytz.timezone('America/Los_Angeles')
        return self.time.astimezone(tz).date()

    class Meta:
        ordering = ['-time'];

class Profile(models.Model):
    user = models.OneToOneField(User)
    start_date = models.DateTimeField('Started', auto_now_add=True)
 
    DAYS_OF_WEEK = (
            ('M', 'Monday'),
            ('T', 'Tuesday'),
            ('W', 'Wednesday'),
            ('H', 'Thursday'),
            ('F', 'Friday'),
            ('S', 'Saturday'),
            ('U', 'Sunday'),
            )
    boost_day = models.CharField(max_length=1, choices=DAYS_OF_WEEK, default=0) 

    STATUS = (
            ('b', 'bronze'),
            ('s', 'silver'),
            ('g', 'gold'),
            )
    status = models.CharField(max_length=1, choices=STATUS, default=0)
    status_value = models.FloatField('status value', default=0)

    last_input_time = models.DateTimeField('Last input time', auto_now_add=True)

    def get_fueluser(self):
        return FuelUser.objects.get(id=self.user.id)

class Record(models.Model):

    user = models.ForeignKey(User)
    date = models.DateField('Date', default='')
    steps = models.PositiveIntegerField('Steps', default=0)
    calories = models.PositiveIntegerField('Calories', default=0)
    fuelscore = models.PositiveIntegerField('FuelScore', default=0)
    amount = models.OneToOneField(Amount)
    last_updated = models.DateTimeField('Last updated', default='', auto_now=True)

    def get_amount(self):
        a = 0
        f = self.fuelscore
        for l,v in zip(POINT_LIMITS, POINT_VALUES):
            a = a + ceil(min(f, l) / float(v))
            if f <= l:
                break
            else:
                f = f - l
        return a

    def save_amount(self):
        a = Amount()
        a.user = self.user
        a.amount = self.get_amount()
        a.atype = 1
        a.time = pytz.utc.localize(datetime.datetime.utcnow())
        a.action = 'FuelScore upload for %s' % self.date.strftime('%m/%d/%y')
        a.save()
        self.amount = a
        self.save()

    class Meta:
        ordering = ['-date'];

class FriendNode(models.Model):

    user = models.OneToOneField(User, blank=True, null=True)
    friends = models.ManyToManyField('self', blank=True, null=True)

    def __unicode__(self):
        return 'FriendNode #%d, friends: %s' % (
                self.id,
                ' '.join([str(x.id) for x in self.friends.all()])
                )

    def add_friend(self, friend):
        self.friends.add(friend)
        self.save()


def import_friendships(filename, count):
    nodes = []
    for i in range(0, count):
        f = FriendNode()
        f.save()
        nodes.append(f)

    with open(filename, 'r') as f:
        for line in f:
            l = [int(x)-1 for x in line.strip().split(' ')]
            print "adding friends %d and %d" % (l[0], l[1])
            nodes[l[0]].add_friend(nodes[l[1]])

def import_users(filename):
    with open(filename, 'r') as f:
        for line in f:
            email,last,first,password = line.strip().split(',')
            
            # search user to make sure he's not instantiated already
            if len(User.objects.filter(email=email)) > 0:
                print "user %s already exists, skipping" % email
                continue

            u = User()
            u.username = email.strip()
            u.first_name = first.strip()
            u.last_name = last.strip()
            u.email = email.strip()
            u.set_password(password.strip())
            u.save()

            # set up profile
            p = Profile()
            p.user = u
            p.boost_day = 'M'
            p.status = 'b'
            p.status_value = 0
            p.save()

            # set up friends
            f = FriendNode.objects.filter(user=None).order_by('?')[0]
            f.user = u
            f.save()

            print "user %s added" % email

### GAME MODELS ###

class Scale(models.Model):
    target = models.IntegerField('target value')
    money = models.FloatField('money')
    active = models.BooleanField(default=True)
    start_time = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey(User, blank=True, null=True)

    @staticmethod
    def create(money=0):
        s = Scale()

        if money == 0:
            target = randint(int(SCALE_MONEY_LIMIT['low'] / POINT_MONEY / 10),
                    int(SCALE_MONEY_LIMIT['high'] / POINT_MONEY / 10)) * 10
            s.target = target
            s.money = target * POINT_MONEY

        if money != 0:
            if money < SCALE_MONEY_LIMIT['low'] or money > SCALE_MONEY_LIMIT['high']:
                print "can't create scale with $%.2f!" % money
                return None
            
            s.target = int(money / POINT_MONEY)
            s.money = money

        s.save()
        return s
    
    def current_value(self):
        return sum([-1 * x.amount for x in self.amount_set.all()])

    def get_money(self):
        return "$%.2f" % self.money
    get_money.short_description = 'Money'

    def set_money(self):
        self.money = target * POINT_MONEY
        self.save()

    def get_end_time(self):
        if self.active:
            return None
        return self.amount_set.all()[0].time

    def get_winner(self):
        return self.winner

    get_winner.short_description = 'Winner'

    def add_amount(self, amount, user):
        if not self.active:
            return None
        amount = int(amount)  #important!
        a = Amount()
        a.user = user
        a.scale = self
        
        ta = self.target - self.current_value()
        if ta <= amount:
            a.amount = -1 * ta
            self.active = False
            self.winner = user
            Scale.create()
        else:
            a.amount = -1 * amount
        a.atype = 3
        a.time = pytz.utc.localize(datetime.datetime.utcnow())
        a.action = 'Scale play' 
        a.save()
        self.save()

        return -1 * a.amount

    def __unicode__(self):
        return 'Scale %d (%s), $%.2f, %d/%d%s' % (
                self.id,
                'active' if self.active else 'finished',
                self.money,
                self.current_value(),
                self.target,
                (', winner: %s' % self.get_winner().get_full_name()) if self.winner is not None else ''
                )


class Project(models.Model):
    members = models.ManyToManyField(User)
    topic = models.CharField('topic', blank=True, max_length=200)
    video = models.CharField(blank=True, max_length=200)

    def get_members(self):
        return ", ".join([m.get_full_name() for m in self.members.all()])
    get_members.short_description='Members'

def import_projects(filename):
    with open(filename, 'r') as fd:
        projects = json.load(fd)
        print projects
        for p in projects:
            project = Project()
            project.topic = p['topic']
            print "Creating project %s" % project.topic
            project.save()
            for m in p['members']:
                print " -- adding member %s" % m
                try:
                    project.members.add(User.objects.get(username=m))
                except:
                    pass
            project.save()
