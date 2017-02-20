# Import the site
from website import site, mail

# Import DB objects
from Model import User, Charity, CharityMember
from DBComm import DB

# Import flask objects
from flask import flash, abort, session, redirect, render_template, url_for

# Import WTForms to handle form templates
from flask.ext.wtf import Form

# Import WTForms helpers
from wtforms import validators
from wtforms.fields import DateField, DateTimeField, HiddenField, TextField, \
       SelectMultipleField, StringField, PasswordField
from wtforms.validators import Required

# Import ItsDangerous for crypyo signing IDs
from itsdangerous import URLSafeSerializer, BadSignature

# Import datetime object
from datetime import datetime

@site.route('/account', methods=['GET'])
def account_home():
    '''
    The user account's home page
    '''
    # Make sure that the session is valid
    if not 'user_id' in session:
        flash(u'You must be logged in first!')
        return redirect(url_for('login'))

    # Validate that the user ID is for an valid user
    # TODO: Add check that the session's user ID is valid
    return render_template('account_home.html')

@site.route('/account/details', methods=['GET', 'POST'])
def account_details():
    '''
    Account details page. Allows user to update information.
    '''
    if not 'user_id' in session:
        flash(u'You must be logged in first!')
        return redirect(url_for('login'))

    return render_template('account_details.html')

@site.route('/account/host-a-dinner', methods=['GET', 'POST'])
def hostdinner():
    '''
    Handles host a dinner page
    '''
    # Make sure that the session is valid
    if not 'user_id' in session:
        flash(u'You must be logged in first!')
        return redirect(url_for('login'))

    form = HostEventForm()

    if form.validate_on_submit():
        # TODO: Add a nice flash message, detailing the event & time
        flash(u'Successfully hosted a dinner for in as %s' % form.event.eventDate)
        # TODO: Add a landing page for hosted events
        return redirect(url_for('hosted-events'))

    flash_errors(form)
    return render_template('host-a-dinner.html', form=form)

@site.route('/', methods=['GET'])
def index():
    '''
    Home page
    '''
    # If there's a user's session, redirect to account
    if 'user_id' in session:
        # TODO: Validate user ID
        return redirect(url_for('account_home'))

    return render_template('index.html', title='Home')

@site.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Handles active user log ins. Checks if
    user is already logged in.
    '''
    if 'user_id' in session:
        # User already has session, redirect to account
        flash(u'You are already logged in!')
        return redirect(url_for('account_home'))

    form = LoginForm()
    if form.validate_on_submit():
        print 'VALID LOGIN'
        flash(u'Successfully logged in as %s' % form.user.userName)
        session['user_id'] = form.user.userID
        return redirect(url_for('account_home'))

    flash_errors(form)
    return render_template('login.html', form=form)

@site.route('/logout', methods=['GET'])
def logout():
    '''
    Handles logging out the active user
    '''
    # Remove the user ID from session
    session.pop('user_id', None)
    return redirect(url_for('index'))

@site.route("/signup", methods=["GET", 'POST'])
def sign_up():
    '''
    Handles new user sign ups
    '''
    # Check if user is already in session
    if 'user_id' in session:
        # Cannot sign up if on your account
        flash (u'Please log out to create a new account.')
        return redirect(url_for('account_home'))

    form = SignupForm()
    if form.validate_on_submit():
        print 'Valid Sign up!'
        flash (u'Signed up successful!')
        session['user_id'] = form.user.userID

        # Now send an email with the verification link
        serializer = URLSafeSerializer(site.secret_key)
        url = serializer.dumps(form.user.userID)

        mail.sendMail(form.user.emailAddress,
                'Eat4Life - Verification Required',
                'Please verify your email: http://localhost:5000/activate/' + url)

        return redirect(url_for('index'))

    flash_errors(form)
    return render_template('signup.html', form=form)

@site.route("/mail", methods=['GET'])
def mail_test():
    '''
    Sends a test email
    '''
    # TODO: Removes this in prod
    mail.sendMail('luis111290@gmail.com', 'Hello!', 'Test Message!')
    return "Sent"

@site.route("/activate/<key>", methods=['GET'])
def activate_user(key):
    '''
    Handles verifying that the user's email account is valid.
    '''
    # Create a serializer using our app's secret key
    serializer = URLSafeSerializer(site.secret_key)
    # Try to load in the key to verify it
    try:
        user_id = serializer.loads(key)
    except BadSignature:
        abort(404)

    # Fetch the user based on the decrypted user ID
    db = DB()
    db.connect()
    # Valid user, update/verify account
    # TODO: Notify user account is valid now, redirect to account screen
    db.verify_user_by_id(user_id)
    db.disconnect()

    return 'Successful!'

@site.route('/genkey/<user_id>', methods=['GET'])
def generate_key(user_id):
    '''
    THIS IS ONLY FOR TESTING. DON'T USE IN PROD
    '''
    # TODO: Remove this once tested that serialization works
    serializer = URLSafeSerializer(site.secret_key)
    url = serializer.dumps(user_id)
    return url

def flash_errors(form):
    '''
    Function expects a Flask WTF Form and will
    flash the error messages in the HTML form.
    '''
    for field, errors in form.errors.items():
        for error in errors:
            flash(
                u"Error in the %s field - %s"
                % (getattr(form, field).label.text,error))

class HostEventForm(Form):
    '''
    Host event form class for validating a host event data
    '''

    event_date = DateField(
        "Event Date", format="%m/%d/%Y",
        validators=[validators.DataRequired()])

    event_time = DateTimeField(
        "Event Time", format="%I:%M %p",
        validators=[validators.DataRequired()])

    event_location_address = StringField('Address', [
        validators.DataRequired(),
        validators.Length(min=2, max=35)])

    event_location_city = TextField('City', [
        validators.DataRequired(),
        validators.Length(min=2, max=35)])

    # TODO: Define a dropdown with the states two char value
    event_location_state = TextField('State', [
        validators.DataRequired(),
        validators.Length(min=2, max=35)])

    event_location_zip = StringField('Zip', [validators.Length(min=5, max=5)])

    # Generate a users list for invitees
    db = DB()
    db.connect()
    usersList = [(user.userName, user.firstName + " " + user.lastName)
            for user in db.getAllVerifiedUsers()]
    db.disconnect()

    event_invitees_list = SelectMultipleField('Invitee List',  choices=usersList)


    def __init__(self, *args, **kwargs):
        '''
        Initializer for event, no event is default.
        '''
        Form.__init__(self, *args, **kwargs)
        self.event = None

    def validate(self):
        '''
        Handles validating the event form data entered in.
        '''

        # Validate our form first
        rv = Form.validate(self)
        if not rv:
            return False

        db = DB()
        db.connect()
        # Make sure there's no event already in place
        # TODO: Add query check if there's another event

        # If there's no event in place, create a new event
        # TODO: Add a query to create a new event
        # new_event = <CREATE_QUERY>
        new_event = None

        # TODO: Create function to add the users/invitees as well

        db.disconnect()

        # Set the login form's user
        self.event = new_event
        return True

class LoginForm(Form):
    '''
    Login class for validating user accounts by
    username and password.
    '''
    username = StringField('Username', [validators.Length(min=2, max=25)])
    password = PasswordField('Password',[validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        '''
        Initializer for login, no user is default.
        '''
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        '''
        Handles validating the user-password entered in.
        '''

        # Validate our form first
        rv = Form.validate(self)
        if not rv:
            return False

        # Connect to DB
        db = DB()
        db.connect()

        # Fetch the user
        user = db.get_user(self.username.data)
        db.disconnect()
        #print user

        # Validate the account's username-pw
        if user is None:
            # No user found
            self.username.errors.append('Invalid login!')
            return False

        if not user.verify_password(self.password.data):
            # Password invalid
            self.password.errors.append('Invalid login!')
            return False

        # Set the login form's user
        self.user = user
        return True

class SignupForm(Form):
    '''
    Signup form class for handling new user account validation.
    '''

    firstname = StringField('First Name', [
        validators.DataRequired(),
        validators.Length(min=2)
    ])
    lastname = StringField('Last Name')
    email = StringField('Email Address', [validators.Length(min=6, max=35)])

    # TODO: Validation on phone? If entered, needs to be certain length
    phone = StringField('Phone Number', [validators.Length(max=10)])

    username = StringField('Username', [
        validators.Length(min=2, max=35),
        validators.DataRequired()
    ])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match!')
    ])
    confirm = PasswordField('Repeat Password')

    def __init__(self, *args, **kwargs):
        '''
        Initializer for signup
        '''
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        '''
        Handles validating the sign up information
        '''

        # Validate our form first
        rv = Form.validate(self)
        if not rv:
            return False

        # TODO: Query to see if the email or username is already taken

        # TODO: Now, insert the new user onto the DB

        db = DB()
        db.connect()

        new_user = db.create_user(self.username.data, self.password.data,
                self.firstname.data, self.lastname.data, self.email.data,
                self.phone.data)

        db.disconnect()

        # Set the login form's user
        self.user = new_user
        return True
