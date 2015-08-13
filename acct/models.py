from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import watson
# Create your models here.
from events.models import Organization


class Profile(models.Model):
    user = models.OneToOneField(User)

    wpibox = models.IntegerField(null=True, blank=True, verbose_name="WPI Box Number")
    phone = models.CharField(max_length=24, null=True, blank=True, verbose_name="Phone Number")
    addr = models.TextField(null=True, blank=True, verbose_name="Address / Office Location")
    mdc = models.CharField(max_length=32, null=True, blank=True, verbose_name="MDC")

    locked = models.BooleanField(default=False)

    @property
    def fullname(self):
        if self.user.first_name and self.user.last_name:
            return self.user.first_name + " " + self.user.last_name
        else:
            return 'Unnamed User (%s)' % self.user.username

    @property
    def email(self):
        return self.user.email

    @property
    def is_lnl(self):
        if self.user.groups.filter(Q(name="Alumni") | Q(name="Active") | Q(name="Officer") | Q(name="Associate") | Q(
                name="Away") | Q(name="Inactive")).exists():
            return True
        else:
            return False

    @property
    def group_str(self):
        groups = map(lambda l: l.name, self.user.groups.all())
        out_str = ""
        if "Alumni" in groups:
            out_str += 'Alum '
        if "Officer" in groups:
            out_str += 'Officer'
        elif "Active" in groups:
            out_str += 'Active'
        elif "Associate" in groups:
            out_str += 'Associate'
        elif "Away" in groups:
            out_str += 'Away'
        elif "Inactive" in groups:
            out_str += 'Inactive'
        else:
            out_str += "Unclassified"
        return out_str

    @property
    def owns(self):
        return ', '.join(map(str, self.user.orgowner.all()))

    @property
    def orgs(self):
        return ', '.join(map(str, self.user.orgusers.all()))

    @property
    def all_orgs(self):
        return Organization.objects.complex_filter(
            Q(user_in_charge=self.user) | Q(associated_users=self.user)).distinct()

    @property
    def mdc_name(self):
        max_chars = 12
        clean_first, clean_last = "", ""

        # assume that Motorola can handle practically nothing. Yes, ugly, but I don't wanna regex 1000's of times
        for char in self.user.first_name.upper().strip():
            if ord(char) == ord(' ') or ord(char) == ord('-') \
                    or ord('0') <= ord(char) <= ord('9') or ord('A') <= ord(char) <= ord('Z'):
                clean_first += char
        for char in self.user.last_name.upper().strip():
            if ord(char) == ord(' ') or ord(char) == ord('-') \
                    or ord('0') <= ord(char) <= ord('9') or ord('A') <= ord(char) <= ord('Z'):
                clean_last += char

        outstr = clean_last[:max_chars - 2] + ","  # leave room for at least an initial
        outstr += clean_first[:max_chars - len(outstr)]  # fill whatever's left with the first name
        return outstr

    class Meta:
        permissions = (
            ('change_group', 'Change the group membership of a user'),
            ('add_user', 'Add a new user'),
            ('edit_mdc', 'Change the MDC of a user'),
            ('edit_user', 'Edit the name and contact info of a user'),
            ('view_user', 'View users'),
            ('view_member', 'View LNL members'),
        )


def create_user_profile(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        profile = Profile.objects.create(user=instance)
        profile.save()
        # if not email, this solves issue #138
        if not instance.email:
            instance.email = "%s@wpi.edu" % instance.username
            instance.save()


post_save.connect(create_user_profile, sender=User)


# hacky? Yes. But I want to fix this, and I don't want to mess with the strangeness of that form.
@receiver(pre_save, sender=Profile)
def check_phone(sender, instance, **kwargs):
    if instance.phone == '(':
        instance.phone = None
    if not instance.wpibox:
        instance.wpibox = None
    if not instance.addr:
        instance.addr = None
    if not instance.mdc:
        instance.mdc = None


class Orgsync_OrgCat(models.Model):
    name = models.CharField(max_length=64)
    orgsync_id = models.IntegerField()

    def __str__(self):
        return "<OrgSyncOrgCat (%s)>" % self.name


class Orgsync_Org(models.Model):
    orgsync_id = models.IntegerField()
    name = models.CharField(max_length=128)
    category = models.ForeignKey(Orgsync_OrgCat, null=True, blank=True)
    keywords = models.TextField(null=True, blank=True)
    president_email = models.EmailField(null=True, blank=True)
    org_email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return "<OrgSyncOrg (%s)>" % self.name


class Orgsync_User(models.Model):
    orgsync_id = models.IntegerField()
    title = models.CharField(max_length=256, null=True, blank=True)
    account_id = models.IntegerField()
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    email_address = models.EmailField()
    memberships = models.ManyToManyField(Orgsync_Org, blank=True)
    last_login = models.DateField(null=True, blank=True)
    about_me = models.TextField(null=True, blank=True)
    portfolio = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return "<OrgSyncUser (%s,%s)>" % (self.first_name, self.last_name)

# example {"id":918421,"title":null,"account_id":575310,"first_name":"Aakriti","last_name":"Bhakhri",
# "picture_url_40":"https://d1nrm4vx8nf098.cloudfront.net/eupwtt1qw06izh_40.jpg",
# "picture_url_60":"https://d1nrm4vx8nf098.cloudfront.net/eupwtt1qw06izh_64.jpg",
# "memberships":[{"id":152541,"name":"Members"}],"email_address":"aakriti@wpi.edu",
# "last_login":"April 24, 2012","portfolio":"http://my.orgsync.com/aakritibhakhri"},
# url https://orgsync.com/38382/accounts?per_page=100&num_pages=3&order=first_name+ASC
# paginatd https://orgsync.com/38382/accounts?per_page=100&num_pages=3&order=first_name+ASC&page=46
# profile https://orgsync.com/profile/display_profile?id=636887
#profile2 https://orgsync.com/profile/display_profile?id=575310
#b.open("https://orgsync.com/38382/groups")
#b.open("https://orgsync.com/38382/accounts?per_page=100&num_pages=3&order=first_name+ASC")
