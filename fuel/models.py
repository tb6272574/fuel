from django.db import models
from django.contrib.auth.models import User
import datetime, pytz
from math import ceil

# constants

DAILY_BONUS = {
        'b': 10,
        's': 30,
        'g': 50
        }

POINT_LIMITS = [2000, 1000, 1e6]
POINT_VALUES = [100, 50, 25]

POINT_MONEY = 0.005

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

    def start_date(self):
        return self.profile.start_date.strftime('%m/%d/%y %H:%M:%S')

    def boost_day(self):
        return BOOST_DAYS[self.profile.boost_day]

    def status(self):
        return STATUS[self.profile.status]

    def current_amount(self):
        return sum([a.amount for a in self.amount_set.all()])  

    def winnings(self):
        return sum([s.money for s in Scale.objects.filter(active=False) if s.get_winner().get_profile().get_fueluser() == self])

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
        a.time = pytz.utc.localize(datetime.datetime.now())
        a.save()

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
        return u"%d" % (self.amount)
    
    def get_date(self):
        tz=pytz.timezone('America/Los_Angeles')
        return self.time.astimezone(tz).date()

    class Meta:
        ordering = ['-time'];

class Profile(models.Model):
    user = models.OneToOneField(User)
    start_date = models.DateTimeField('Started', default='', auto_now_add=True)
 
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

    last_input_time = models.DateTimeField('Last input time', default='')

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
            a = a + ceil(min(f, l) / v)
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
        a.time = pytz.utc.localize(datetime.datetime.now())
        a.action = 'FuelScore upload for %s' % self.date.strftime('%m/%d/%y')
        a.save()
        self.amount = a
        self.save()


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


### GAME MODELS ###

class Scale(models.Model):
    target = models.IntegerField('target value')
    money = models.FloatField('money')
    active = models.BooleanField(default=True)
    start_time = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def create(money):
        s = Scale()
        s.target = int(money / POINT_MONEY)
        s.money = money
        s.save()
        return s
    
    def current_value(self):
        return sum([-1 * x.amount for x in self.amount_set.all()])

    def set_money(self):
        self.money = target * POINT_MONEY
        self.save()

    def get_winner(self):
        if self.active:
            return None
        return self.amount_set.all()[0].user

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
        else:
            a.amount = -1 * amount
        a.atype = 3
        a.time = pytz.utc.localize(datetime.datetime.now())
        a.action = 'Scale play' 
        a.save()
        self.save()

        return -1 * a.amount

    def __unicode__(self):
        return 'Scale %d (%s), $%.2f, target %d, current %d%s' % (
                self.id,
                'active' if self.active else 'finished',
                self.money,
                self.target,
                self.current_value(),
                (', winner: %s' % self.get_winner().get_full_name()) if not self.active else ''
                )





