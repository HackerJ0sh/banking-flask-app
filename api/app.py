from flask import Flask, flash, render_template, redirect, url_for, request, session
from flask_login import LoginManager, current_user, logout_user, UserMixin, login_user, login_required
from datetime import timedelta  # perma session
import datetime
from flask_sqlalchemy import SQLAlchemy  # the creation of data base
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "hello"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False    # removes warning
app.permanent_session_lifetime = timedelta(days=2)    # store data for 2 days

# flask login stuff

login_manager = LoginManager(app)
login_manager.login_view = 'login'   # redirects them to login when not login users try to access logged in pages

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


db = SQLAlchemy(app)

# create db models
class Users(db.Model, UserMixin):
    id = db.Column("id", db.Integer, primary_key=True)   # each column name is unique
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    pin_number = db.Column(db.String(100))
    balance = db.Column(db.Integer)
    card_number = db.Column(db.String(100))
    card_cvv = db.Column(db.String(100))
    card_holder_name = db.Column(db.String(100))
    transaction = db.relationship('Transactions', backref='users')


    def __init__(self, username, password, balance, card_number, card_cvv, card_holder_name, pin_number, transaction): 
        self.username = username
        self.password = password
        self.balance = balance
        self.card_number = card_number
        self.card_cvv = card_cvv
        self.card_holder_name = card_holder_name
        self.pin_number = pin_number
        self.transaction = transaction
        
class Transactions(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    date = db.Column(db.String(100))
    time = db.Column(db.String(100))
    transaction_amt = db.Column(db.Integer())
    transfered_user = db.Column(db.String(100))
    receive_user = db.Column(db.String(100))
    user = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))   

    def __init__(self, date, time, transaction_amt, transfered_user, receive_user):
        self.date = date
        self.time = time
        self.transaction_amt = transaction_amt
        self.transfered_user = transfered_user
        self.receive_user = receive_user



@app.route('/') 
def home():
    title = 'home'
    return render_template('home.html', title=title)

@app.route('/login', methods=["POST", "GET"])
def login(): 
    title = 'login'
    if request.method == "POST": 
        session.permanent = True    # sets the perma session to the defined time above
        user = request.form['login-user']
        password = request.form['login-pwd']

        # check for user in db 

        found_user = Users.query.filter_by(username=user).first()  # find the user object

        if found_user:
            if check_password_hash(found_user.password, password):
                session['balance'] = found_user.balance   # retrieve data from data and store in session
                session['user'] = found_user.username
                session['card_num'] = found_user.card_number
                session['card_cvv'] = found_user.card_cvv
                session['card_name'] = found_user.card_holder_name
                session['pin-number'] = found_user.pin_number

                login_user(found_user, remember=True)

                flash(f'Welcome back, {user}.')

                return redirect(url_for('user_home_page'))
            else:
                flash('Wrong Password')
                return redirect(url_for('login'))
        else:                                               # user not found
            flash(f'User with username {user} not found.')

            return redirect(url_for('signup'))

    else: 
        return render_template('login.html', title=title)   # if not login it renders login page



@app.route('/logout')
@login_required
def logout(): 
    user = session['user']
    session.pop('user', None)
    session.pop('balance', None)     # deleting the session data on the client side
    session.pop('card_num', None)
    session.pop('card_cvv', None)
    session.pop('card_name', None)
    session.pop('pin-number', None)
    logout_user()
    flash(f'See you soon {user}.')
    return redirect(url_for('home'))
    
@app.route('/withdraw', methods=["POST", "GET"])
@login_required
def withdraw():
    user = session['user']
    balance = int(session['balance'])
    card_number = session['card_num']
    card_cvv = session['card_cvv']
    card_name = session['card_name']
    pin_number = session['pin-number']
    found_user = Users.query.filter_by(username=user).first()

    transaction_history = found_user.transaction # list of all transaction objects 

    if request.method == "POST":
        try:
            withdraw_amt = int(request.form['withdraw-amt'])
        except ValueError:
            flash('Please enter a number.')
            return redirect(url_for('withdraw'))
        
        withdraw_pin_number = request.form['withdraw-pin']
        
        if withdraw_amt <= balance and withdraw_amt > 0: 
            if withdraw_pin_number == pin_number:
                balance -= withdraw_amt
                session['balance'] = balance

                found_user.balance = balance

                # for Transaction history
                init_datetime = datetime.datetime.now()

                date = init_datetime.strftime('%d') + '-' + init_datetime.strftime('%m') + '-' + init_datetime.strftime('%Y')
                time = init_datetime.strftime('%H') + ':' + init_datetime.strftime('%M') + ':' + init_datetime.strftime('%S')
                withdraw_transaction = Transactions(date=date, time=time, transaction_amt= "-$" + str(withdraw_amt), transfered_user=user, receive_user="-")

                db.session.add(withdraw_transaction)

                found_user.transaction.append(withdraw_transaction)
                db.session.add(found_user)
            
                db.session.commit()

                flash(f'Withdrawed ${withdraw_amt} successfully.')

                return redirect(url_for('user_home_page'))
            else:
                flash('Pin number is incorrect.')
                return redirect(url_for('withdraw'))
        
        elif withdraw_amt > balance:
            flash('You cannot withdraw more than your balance.')
            return redirect(url_for('withdraw'))
        
        else: 
            flash('Please enter a positve number.')
            return redirect(url_for('withdraw'))
    else: 
        return render_template('withdraw.html', balance=balance, card_number=card_number, card_cvv=card_cvv, card_name=card_name, transaction_history=transaction_history)


@app.route('/deposit', methods=["POST", "GET"])
@login_required
def deposit():
    user = session['user']
    balance = int(session['balance'])
    card_number = session['card_num']
    card_cvv = session['card_cvv']
    card_name = session['card_name']
    pin_number = session['pin-number']
    found_user = Users.query.filter_by(username=user).first()

    transaction_history = found_user.transaction # list of all transaction objects 
    print(transaction_history)

    if request.method == "POST":
        try:
            deposit_balance = int(request.form['deposit-amt'])
        except ValueError:
            flash('Please enter a number.')
            return redirect(url_for('deposit'))
        
        deposit_pin_number = request.form['deposit-pin']
        
        if deposit_balance > 0: 
            if pin_number == deposit_pin_number:
                balance += deposit_balance
                session['balance'] = balance

                found_user.balance = balance

                # for Transaction history
                init_datetime = datetime.datetime.now()

                date = init_datetime.strftime('%d') + '-' + init_datetime.strftime('%m') + '-' + init_datetime.strftime('%Y')
                time = init_datetime.strftime('%H') + ':' + init_datetime.strftime('%M') + ':' + init_datetime.strftime('%S')
                deposit_transaction = Transactions(date=date, time=time, transaction_amt= "+$" + str(deposit_balance), transfered_user=user, receive_user="-")

                db.session.add(deposit_transaction)

                found_user.transaction.append(deposit_transaction)
            
                db.session.add(found_user)
                db.session.commit()

                flash(f'Deposited ${deposit_balance} successfully.')

                return redirect(url_for('user_home_page'))
            else: 
                flash('Pin number is incorrect.')
                return redirect(url_for('deposit'))
        else:
            flash('Please enter a positive number.')
            return redirect(url_for('deposit'))
    else: 
        return render_template('deposit.html', balance=balance, card_number=card_number, card_cvv=card_cvv, card_name=card_name, transaction_history=transaction_history)




@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "POST": 
        session.permanent = True
        user = request.form['signup-user']
        session['user'] = user

        all_user = Users.query.filter_by(username=user).first()
        if all_user:
            if all_user.username == user: 
                flash(f'Username: {user} already exists. Please enter another username.')
                return redirect(url_for('signup'))
        
        # create user 

        new_user = Users(user, "", "", "", "", "", "", [])  
        session['user'] = new_user.username    # store user in session 
        db.session.add(new_user)
        db.session.commit()
            
        # check if both password are the same
        password = request.form['signup-pwd']
        repeat_password = request.form['signup-repeat-pwd']

        if len(password) > 8:
            if password != user:
                if password == repeat_password:
                    new_user.password = generate_password_hash(repeat_password, method="pbkdf2:sha256")
                    db.session.add(new_user)
                    db.session.commit()
                else:
                    flash('Password does not match.')
                    return redirect(url_for('signup'))
            else: 
                flash('Password cannot be equal to your username.')
                return redirect(url_for('signup'))
        else: 
            flash('Password length is too short, must have a minumum of 8 characters.')
            return redirect(url_for('signup'))


            # added hash pw to db 

        # adding balance to db and pin number
        balance = request.form['signup-balance']
        pin_number = request.form['signup-pin']
        new_user.balance = balance
        new_user.pin_number = pin_number
        session['balance'] = new_user.balance
        session['pin-number'] = pin_number
        db.session.add(new_user)
        db.session.commit()

        # get card details 

        card_number = request.form['signup-card-num']
        card_cvv = request.form['signup-card-cvv']
        card_holder_name = request.form['signup-card-name'].upper()

        session['card_num'] = card_number
        session['card_cvv'] = card_cvv
        session['card_name'] = card_holder_name

        # check for the cvv, card name
        if len(card_cvv) == 3:
            if len(card_number) == 16:
                first_set_digits = card_number[0:4]
                second_set_digits = card_number[4:8]
                third_set_digits = card_number[8:12]
                fourth_set_digits = card_number[12:16]
                card_number_list = [first_set_digits, second_set_digits, third_set_digits, fourth_set_digits]
                card_number = '-'.join(card_number_list)
                session['card_num'] = card_number

                new_user.card_number = card_number
                new_user.card_cvv = card_cvv
                new_user.card_holder_name = card_holder_name
                db.session.add(new_user)
                db.session.commit()
            else:
                flash('Invalid card number length.')
                return redirect(url_for('signup'))
        else:
            flash('Invalid CVV length.')
            return redirect(url_for('signup'))


        login_user(new_user, remember=True)

        flash('Thank You for entrusting us with your banking transactions.')

        return render_template('user.html', user=user, balance=balance)

    else:
        return render_template('signup.html')
    

@app.route('/user-home-page')
@login_required
def user_home_page():
    balance = session['balance']
    user = session['user']
    return render_template('user.html', user=user, balance=balance)

@app.route('/transfer', methods=["POST", "GET"])
@login_required
def transfer():
    # TODO: make the transfer template 
    # TODO: transfer plan -- filter find user if user not found then say user not found
    pin_number = session['pin-number']
    balance = int(session['balance'])
    card_number = session['card_num']
    card_cvv = session['card_cvv']
    card_name = session['card_name']
    user = session['user']
    concurrent_user = Users.query.filter_by(username=user).first()
    
    transaction_history = concurrent_user.transaction
    print(transaction_history)
    if request.method == "POST":

        transfer_user = request.form['transfer-user']
        try:
            transfer_amt = int(request.form['transfer-amt'])
        except ValueError:
            flash('Please enter a numerical value.')
            return redirect(url_for('transfer'))
        
        transfer_pin_number = request.form['transfer-pin']

        found_user = Users.query.filter_by(username=transfer_user).first()
        curr_user = Users.query.filter_by(username=user).first()

        transaction_history = found_user.transaction

        if found_user:
            if transfer_amt > 0 and transfer_amt <= balance:
                if transfer_pin_number == pin_number:
                    # minus balance from curr user
                    curr_user.balance -= transfer_amt
                    found_user.balance += transfer_amt

                    # for Transaction history
                    init_datetime = datetime.datetime.now()

                    date = init_datetime.strftime('%d') + '-' + init_datetime.strftime('%m') + '-' + init_datetime.strftime('%Y')
                    time = init_datetime.strftime('%H') + ':' + init_datetime.strftime('%M') + ':' + init_datetime.strftime('%S')
                    transfer_transaction = Transactions(date=date, time=time, transaction_amt= "-$" + str(transfer_amt), transfered_user=user , receive_user=transfer_user)
                    transfer_transaction_user = Transactions(date=date, time=time, transaction_amt= "+$" + str(transfer_amt), transfered_user=user, receive_user=transfer_user)

                    db.session.add(transfer_transaction)
                    db.session.add(transfer_transaction_user)


                    curr_user.transaction.append(transfer_transaction)
                    found_user.transaction.append(transfer_transaction_user)

                    db.session.add(curr_user)
                    db.session.add(found_user)
                    
                        
                    db.session.commit() 

                    session['balance'] = curr_user.balance

                    flash(f'Successfully transfered ${transfer_amt} to {transfer_user}')
                    return redirect(url_for('transfer'))
                else: 
                    flash('Pin number incorrect.')
                    return redirect(url_for('transfer'))
            else:
                flash('Please ensure that amount you are transfering is a positive number and not more than your balance.')
                return redirect(url_for('transfer'))
        else:
            flash('The user that you want to transfer to, does not exist.')
            return redirect(url_for('transfer'))
    else:
        return render_template('transfer.html', balance=balance, card_number=card_number, card_cvv=card_cvv, card_name=card_name, transaction_history=transaction_history)


if __name__ == '__main__': 
    with app.app_context():
        db.create_all()   # to create the database file
    app.run(debug=True, port=8000)


# the bug is