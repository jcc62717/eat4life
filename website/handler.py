# Import the site
from website import site

# Import DB objects
from Model import User, Charity, CharityMember
from DBComm import DB

# Import flask objects
from flask import flash, abort, session, redirect, render_template, url_for

# Import flask WTF Forms to handle login validation
from flask.ext.wtf import Form
from wtforms import validators
from wtforms.fields import TextField, StringField, PasswordField
from wtforms.validators import Required

# Import ItsDangerous for crypyo signing IDs
from itsdangerous import URLSafeSerializer, BadSignature

@site.route('/', methods=['GET'])
def index():
    '''
    Home page
    '''
    return render_template('index.html', title='Home')

@site.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Handles active user log ins. Checks if
    user is already logged in.
    '''
    form = LoginForm()
    if form.validate_on_submit():
        print 'VALID LOGIN'
        flash(u'Successfully logged in as %s' % form.user.userName)
        #session['user_id'] = form.user[0]
        return redirect(url_for('index'))

    return render_template('login.html', form=form)

@site.route("/signup", methods=["GET", 'POST'])
def sign_up():
    '''
    Handles new user sign ups
    '''
    form = SignupForm()
    if form.validate_on_submit():
        print 'Valid Sign up!'
        flash (u'Signed up successful!')
        #session['user_id'] = form.user[0]
        return redirect(url_for('index'))

    return render_template('signup.html', form=form)

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
    print user_id

    # Fetch the user based on the decrypted user ID
    db = DB()
    db.connect()
    user = db.get_user_by_id(user_id)
    db.disconnect()

    if user is None:
        # Invalid user found
        print 'Invalid verification, user not found'
        abort(404)
    else:
        # TODO: Activate user account
        # TODO: Notify user account is valid now, redirect to account screen
        return "Valid account verification!"

@site.route('/genkey/<user_id>', methods=['GET'])
def generate_key(user_id):
    '''
    THIS IS ONLY FOR TESTING. DON'T USE IN PROD
    '''
    # TODO: Remove this once tested that serialization works
    serializer = URLSafeSerializer(site.secret_key)
    url = serializer.dumps(user_id)
    return url

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

        if not user.check_password(self.password.data):
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

        # TODO: We'll need a flag on the users table (IsValidated)
        # TODO: We'll need to send a verification email to email address.
        # Once user is vaidated, update flag and then allow user
        # to access account

        #user = db.get_user(self.username.data)
        #print user
        db.disconnect()

        # Set the login form's user
        self.user = new_user
        return True
