# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AccountEmailaddress(models.Model):
    email = models.CharField(unique=True, max_length=254)
    verified = models.BooleanField()
    primary = models.BooleanField()
    user = models.ForeignKey('AuthUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailaddress'


class AccountEmailconfirmation(models.Model):
    created = models.DateTimeField()
    sent = models.DateTimeField(blank=True, null=True)
    key = models.CharField(unique=True, max_length=64)
    email_address = models.ForeignKey(AccountEmailaddress, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailconfirmation'


class AccountsUserprofile(models.Model):
    subscription = models.BooleanField()
    user = models.OneToOneField('AuthUser', models.DO_NOTHING, blank=True, null=True)
    email_verified = models.BooleanField()
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    dark_mode = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'accounts_userprofile'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class FeaturesMasterInstrumentsOptionsV(models.Model):
    trading_symbol = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    strike_price = models.CharField(max_length=200, blank=True, null=True)
    strike = models.CharField(max_length=200, blank=True, null=True)
    instrument_type = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'features_master_instruments_options_v'


class FiiDiiCash(models.Model):
    date = models.DateField(blank=True, null=True)
    fii_gross_purchase = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fii_gross_sales = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fii_net_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dii_gross_purchase = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dii_gross_sales = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dii_net_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fii_dii_cash'


class HomeResponse(models.Model):
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=200, blank=True, null=True)
    body = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'home_response'


class IndexOptionHistory(models.Model):
    date = models.DateTimeField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    strike = models.IntegerField(blank=True, null=True)
    instrument_type = models.CharField(max_length=-1, blank=True, null=True)
    expiry_date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    oi = models.BigIntegerField(blank=True, null=True)
    underlying = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'index_option_history'
        unique_together = (('date', 'ticker'),)


class IndexOptionHistoryDay(models.Model):
    date = models.DateTimeField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    strike = models.IntegerField(blank=True, null=True)
    instrument_type = models.CharField(max_length=-1, blank=True, null=True)
    expiry_date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    oi = models.BigIntegerField(blank=True, null=True)
    underlying = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'index_option_history_day'
        unique_together = (('date', 'ticker'),)


class IndexOptionHistoryDaySample(models.Model):
    date = models.DateTimeField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    strike = models.IntegerField(blank=True, null=True)
    instrument_type = models.CharField(max_length=-1, blank=True, null=True)
    expiry_date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    oi = models.BigIntegerField(blank=True, null=True)
    underlying = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'index_option_history_day_sample'
        unique_together = (('date', 'ticker'),)


class IndexOptionHistoryTest(models.Model):
    date = models.DateTimeField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    strike = models.IntegerField(blank=True, null=True)
    instrument_type = models.CharField(max_length=-1, blank=True, null=True)
    expiry_date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    oi = models.BigIntegerField(blank=True, null=True)
    underlying = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'index_option_history_test'
        unique_together = (('date', 'ticker'),)


class Kiteauth(models.Model):
    api_key = models.CharField(max_length=100, blank=True, null=True)
    api_secret = models.CharField(max_length=100, blank=True, null=True)
    access_token = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kiteauth'


class MasterInstruments(models.Model):
    instrument_token = models.CharField(max_length=50)
    exchange_token = models.CharField(max_length=50)
    tradingsymbol = models.CharField(max_length=100)
    name = models.CharField(max_length=50, blank=True, null=True)
    last_price = models.FloatField()
    expiry = models.DateField(blank=True, null=True)
    strike = models.FloatField()
    tick_size = models.DecimalField(max_digits=4, decimal_places=2)
    lot_size = models.IntegerField()
    instrument_type = models.CharField(max_length=5)
    segment = models.CharField(max_length=10)
    exchange = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'master_instruments'


class MaxpainHistory(models.Model):
    date = models.DateField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    expiry_date = models.DateField()
    maxpain_value = models.FloatField(blank=True, null=True)
    spot_price = models.FloatField(blank=True, null=True)
    call_oi = models.IntegerField(blank=True, null=True)
    put_oi = models.IntegerField(blank=True, null=True)
    pcr = models.FloatField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'maxpain_history'
        unique_together = (('date', 'ticker', 'expiry_date'),)


class PostOfficeAttachment(models.Model):
    file = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=255)
    headers = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'post_office_attachment'


class PostOfficeAttachmentEmails(models.Model):
    attachment = models.ForeignKey(PostOfficeAttachment, models.DO_NOTHING)
    email = models.ForeignKey('PostOfficeEmail', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'post_office_attachment_emails'
        unique_together = (('attachment', 'email'),)


class PostOfficeEmail(models.Model):
    from_email = models.CharField(max_length=254)
    to = models.TextField()
    cc = models.TextField()
    bcc = models.TextField()
    subject = models.CharField(max_length=989)
    message = models.TextField()
    html_message = models.TextField()
    status = models.SmallIntegerField(blank=True, null=True)
    priority = models.SmallIntegerField(blank=True, null=True)
    created = models.DateTimeField()
    last_updated = models.DateTimeField()
    scheduled_time = models.DateTimeField(blank=True, null=True)
    headers = models.TextField(blank=True, null=True)
    context = models.TextField(blank=True, null=True)
    template = models.ForeignKey('PostOfficeEmailtemplate', models.DO_NOTHING, blank=True, null=True)
    backend_alias = models.CharField(max_length=64)
    number_of_retries = models.IntegerField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    message_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'post_office_email'


class PostOfficeEmailtemplate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    subject = models.CharField(max_length=255)
    content = models.TextField()
    html_content = models.TextField()
    created = models.DateTimeField()
    last_updated = models.DateTimeField()
    default_template = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    language = models.CharField(max_length=12)

    class Meta:
        managed = False
        db_table = 'post_office_emailtemplate'
        unique_together = (('name', 'language', 'default_template'),)


class PostOfficeLog(models.Model):
    date = models.DateTimeField()
    status = models.SmallIntegerField()
    exception_type = models.CharField(max_length=255)
    message = models.TextField()
    email = models.ForeignKey(PostOfficeEmail, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'post_office_log'


class SocialAuthAssociation(models.Model):
    server_url = models.CharField(max_length=255)
    handle = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'social_auth_association'
        unique_together = (('server_url', 'handle'),)


class SocialAuthCode(models.Model):
    email = models.CharField(max_length=254)
    code = models.CharField(max_length=32)
    verified = models.BooleanField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'social_auth_code'
        unique_together = (('email', 'code'),)


class SocialAuthNonce(models.Model):
    server_url = models.CharField(max_length=255)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=65)

    class Meta:
        managed = False
        db_table = 'social_auth_nonce'
        unique_together = (('server_url', 'timestamp', 'salt'),)


class SocialAuthPartial(models.Model):
    token = models.CharField(max_length=32)
    next_step = models.SmallIntegerField()
    backend = models.CharField(max_length=32)
    data = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'social_auth_partial'


class SocialAuthUsersocialauth(models.Model):
    provider = models.CharField(max_length=32)
    uid = models.CharField(max_length=255)
    extra_data = models.TextField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    created = models.DateTimeField()
    modified = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'social_auth_usersocialauth'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialaccount(models.Model):
    provider = models.CharField(max_length=30)
    uid = models.CharField(max_length=191)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    extra_data = models.TextField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialaccount'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialapp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=191)
    secret = models.CharField(max_length=191)
    key = models.CharField(max_length=191)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp'


class SocialaccountSocialappSites(models.Model):
    socialapp = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp_sites'
        unique_together = (('socialapp', 'site'),)


class SocialaccountSocialtoken(models.Model):
    token = models.TextField()
    token_secret = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)
    account = models.ForeignKey(SocialaccountSocialaccount, models.DO_NOTHING)
    app = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialtoken'
        unique_together = (('app', 'account'),)


class StockFuturesHistoryDay(models.Model):
    date = models.DateTimeField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    expiry_date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    oi = models.BigIntegerField(blank=True, null=True)
    underlying = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_futures_history_day'
        unique_together = (('date', 'ticker'),)


class StockOhlc(models.Model):
    date = models.DateTimeField()
    ticker = models.CharField(max_length=-1)
    instrument_token = models.IntegerField(blank=True, null=True)
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    exchange = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_ohlc'


class StockOptionHistory(models.Model):
    date = models.DateTimeField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    strike = models.IntegerField(blank=True, null=True)
    instrument_type = models.CharField(max_length=-1, blank=True, null=True)
    expiry_date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    oi = models.BigIntegerField(blank=True, null=True)
    underlying = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_option_history'
        unique_together = (('date', 'ticker'),)


class StockOptionHistoryDay(models.Model):
    date = models.DateTimeField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    strike = models.IntegerField(blank=True, null=True)
    instrument_type = models.CharField(max_length=-1, blank=True, null=True)
    expiry_date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    oi = models.BigIntegerField(blank=True, null=True)
    underlying = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_option_history_day'
        unique_together = (('date', 'ticker'),)


class StockOptionHistoryDaySample(models.Model):
    date = models.DateTimeField(primary_key=True)
    ticker = models.CharField(max_length=-1)
    strike = models.IntegerField(blank=True, null=True)
    instrument_type = models.CharField(max_length=-1, blank=True, null=True)
    expiry_date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.BigIntegerField(blank=True, null=True)
    oi = models.BigIntegerField(blank=True, null=True)
    underlying = models.CharField(max_length=-1, blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_option_history_day_sample'
        unique_together = (('date', 'ticker'),)
