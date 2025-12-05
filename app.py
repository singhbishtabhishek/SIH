from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import and_,or_, func, join
from datetime import datetime
from sqlalchemy.exc import IntegrityError 

app= Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///travell.sqlite3"  
db = SQLAlchemy(app)
app.app_context().push()

app.secret_key = 'in_secrest_key_we_add_a_long_string_and_do_not_share_this_string_with_anyone_6178101002.'

with app.app_context():
    db.create_all()

################################################ all the database models ######################################################

class users(db.Model):
    # this is the primary key for this table and even stored in session 
    username = db.Column(db.String(12), primary_key=True) 
    # customer's name
    name = db.Column(db.String(50), nullable=False) 
    # It is a unique attribute, stored in session 
    # A user can not register with same email more than one time 
    email = db.Column(db.String(100), unique=True, nullable=False) 
    # email of costomer
    password = db.Column(db.String(15), nullable=False)
    # Customer or Manager as the register is existing for user only thus, default value is customer.
    role = db.Column(db.String(10), default='customer', nullable=False) 
    phone = db.Column(db.Numeric(10, 0), nullable=False) # A 10-digit phone no.
    address = db.Column(db.String(50), nullable=False)
    # gender field with specified values 
    gender = db.Column(db.Enum('male', 'female', 'other', name='gender_enum'), nullable=False)


class managers(db.Model):
    username = db.Column(db.String(12), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(15), nullable=False)
    # default value should be stored as manager
    role = db.Column(db.String(10), default='admin', nullable=False)  
    phone = db.Column(db.Numeric(10, 0), nullable=False)
    address = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.Enum('male', 'female', 'other', name='gender_enum'), nullable=False)


class state(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    
    s_name = db.Column(db.String(50), nullable=False, unique=True)
    s_description = db.Column(db.Text, nullable=True)
    s_id = db.Column(db.String(10), nullable=False, unique=True)
    s_image = db.Column(db.String(200), nullable=True)


class places(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    p_id = db.Column(db.String(50), unique=True, nullable=False) 
    s_id = db.Column(db.String(50), db.ForeignKey('state.s_id'), nullable=False)
    p_name = db.Column(db.String(100), unique=True, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(100), nullable=True)  # Optional for GPS coordinates
    p_image = db.Column(db.String(200), nullable=True)
    # measuring base  
    unit = db.Column(db.String(50), nullable=False) 
    # price of single unit
    unit_price = db.Column(db.DECIMAL(10, 0), nullable=False)
    # no: of units initially present in stock or no: of units purchased
    qty_stock = db.Column(db.Integer, nullable=False) 
    # number of units sold  
    qty_sold = db.Column(db.Integer)

    ''' 
        Meanings are as follows:
            here 'I' ----> IN STOCK
            here 'O' ----> STOCK OUT

    '''
    availability = db.Column(db.String(1), db.CheckConstraint("availability IN ('I', 'O')"))
    # relationships
    state = db.relationship("state", backref="places")

# this is the database model for the cart in which products are added by the users

class cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    u_id = db.Column(db.String(12), db.ForeignKey('users.username'), nullable=False) # username of user
    s_id = db.Column(db.String(10), db.ForeignKey('state.s_id'), nullable=False) # category id
    p_id = db.Column(db.String(50), db.ForeignKey('places.p_id'), nullable=False) # product id
    # number of units user wants to purchase
    qty = db.Column(db.Integer, nullable=False, default=0)  
    unit_price = db.Column(db.DECIMAL(10, 0), nullable=False) 
    # calculation formula ----> price = ( qty X unit_price )    
    price = db.Column(db.Integer, nullable=False) 
    cart_id = db.Column(db.Integer, nullable=True)# cart id for the user 
    # keep in mind that cart bill. no. will be 0
    bill_no = db.Column(db.Integer, nullable=True) 
    date_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False) # auto-filled based on date and time 
    # relationships
    user = db.relationship("users", foreign_keys=[u_id])
    state = db.relationship("state", foreign_keys=[s_id])
    places = db.relationship("places", foreign_keys=[p_id])

# this is the database model for the sales, in which the inventory managing takes place 

class sales(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    u_id = db.Column(db.String(12), db.ForeignKey('users.username'), nullable=False)
    s_id = db.Column(db.String(10), db.ForeignKey('state.s_id'), nullable=False)
    p_id = db.Column(db.String(50), db.ForeignKey('places.p_id'), nullable=False)

    qty = db.Column(db.Integer, nullable=False, default=0)
    unit_price = db.Column(db.DECIMAL(10, 0), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    cart_id = db.Column(db.Integer, nullable=True)

    # previous default bill no 0 gets update with bill. no.
    bill_no = db.Column(db.Integer, nullable=True)
    date_time = db.Column(db.DateTime,nullable=False)
    billing_date_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False) # its the time and date of billing
    # relationships
    user = db.relationship("users", foreign_keys=[u_id])
    state = db.relationship("state", foreign_keys=[s_id])
    places = db.relationship("places", foreign_keys=[p_id])


################################################ all the database models ends here ######################################################

@app.route('/thankyou')  
def thankyou():
# html page is home.html
    return render_template('thankyou.html') 


@app.route('/')  
def home():
# html page is home.html
    return render_template('home.html') 

################################################ MANAGER PAGE FUNCTIONS START ######################################################


@app.route('/admin_login') # route to go to the manager / admin login.
def admin_login():

    return render_template('admin_login1.html')

#---------------------- checking the credential added in login form -------------------------#

@app.route('/admin_login_check', methods=['POST'])
def admin_login_check():

    if request.method == 'POST':

        email = request.form.get('email')
        # printing email # print(email)
        password = request.form.get('password')
        # print(password)
        #query for checking manager
        user = managers.query.filter(and_(managers.email == email, managers.password == password)).first() 

        if user:
            # if user is present store the email in session
            session['email'] = user.email 
            session['username'] = user.username 
            return redirect(url_for('admin_dashboard'))  
    return redirect(url_for('admin_login'))


#------------- if credential are present in the manager table redirecting to the manager dashboard ----------------#


@app.route('/admin_dashboard')
def admin_dashboard():
    # Fetch all states from the database
    states = state.query.all()  # Adjusted to fetch from the State model
    # 'Guest' is the default value for error handling
    username = session.get('username', 'Guest')
    return render_template('admin_dashboard.html', username=username, states=states)

#------------- category ----> create, delete, update  ----------------#

@app.route('/create_state')
def create_state():
    # Storing the username from session in a variable
    username = session.get('username', 'Guest')
    return render_template('create_state.html', username=username)

#------------- category ----> create  ----------------#

# addes just now 

@app.route('/add_state', methods=['POST'])
def add_state():
    if request.method == 'POST':
        state_id = request.form['state_id']
        state_name = request.form['StateName']
        state_description = request.form['StateDescription']
        state_image = request.form['StateImage']
        
        new_state = state(
            s_id=state_id, 
            s_name=state_name, 
            s_description=state_description, 
            s_image=state_image
        )
        
        db.session.add(new_state)
        db.session.commit()
        return redirect(url_for('admin_dashboard')) 
    return redirect(url_for('create_state'))

#------------- category ----> update  ----------------#

@app.route('/edit_state/<int:state_id>', methods=['GET', 'POST'])
def edit_state(state_id):
    # Logic for editing the state
    current_state = state.query.get_or_404(state_id)  # Use a different variable name
    
    if request.method == 'POST':
        # Get updated data from the form
        current_state.s_name = request.form['s_name']
        current_state.s_description = request.form['s_description']
        current_state.s_image = request.form['s_image']
        
        # Commit changes to the database
        db.session.commit()
        flash('State updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # If the request is GET, render the edit form with current state data
    return render_template('edit_state.html', state=current_state)

#------------- category ----> delete ----------------#

@app.route('/delete_state/<int:state_id>', methods=['POST'])
def delete_state(state_id):
    # Query the state by ID
    current_state = state.query.get_or_404(state_id)  # Use a different variable name
    
    # Delete the state from the database
    db.session.delete(current_state)
    db.session.commit()
    
    flash('State deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

#------------- category working (ends) ----> create, delete, update  ----------------#

@app.route('/create_places', methods=['GET'])
def create_places():
    # Taking the user name from the session; if not stored, display 'Guest'.
    username = session.get('username', 'Guest')
    s_id = request.args.get('s_id')  # Get the state ID from the query string
    return render_template('create_places.html', username=username, s_id=s_id)

#------------- product ----> create ----------------#

@app.route('/add_places', methods=['GET', 'POST'])
def add_places():
    # Taking the user name from the session; if not stored, display 'Guest'.
    username = session.get('username', 'Guest')

    if request.method == 'POST':
        # Get data from the form
        p_id = request.form['p_id']
        s_id = request.form['s_id']
        p_name = request.form['p_name']
        city = request.form['city']
        address = request.form['address']
        location = request.form['location']
        p_image = request.form['p_image']
        unit = request.form['unit']
        unit_price = request.form['unit_price']
        qty_stock = request.form['qty_stock']
        qty_sold = request.form['qty_sold']
        availability = request.form['availability']

        # Create a new place instance
        new_place = places(
            p_id=p_id,
            s_id=s_id,
            p_name=p_name,
            city=city,
            address=address,
            location=location,
            p_image=p_image,
            unit=unit,
            unit_price=unit_price,
            qty_stock=qty_stock,
            qty_sold=qty_sold,
            availability=availability
        )

        # Add to the session and commit to the database
        db.session.add(new_place)
        db.session.commit()

        flash('Place created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('create_places.html', username=username)


#------------- places ----> view ----------------#

@app.route('/view_places')
def view_places():
    s_id = request.args.get('s_id')  # Get the state ID from the query string
    places_list = places.query.filter_by(s_id=s_id).all()  # Query places associated with the state
    return render_template('admin_view_places.html', places=places_list)

#------------- product ----> edit ----------------#


@app.route('/edit_places/<string:place_id>', methods=['GET', 'POST'])
def edit_places(place_id):
    # Fetch the place from the database using the place_id
    place_edit = places.query.filter_by(p_id=place_id).first()  # Adjust the query as needed

    if request.method == 'POST':
        # Get data from the form
        p_id = request.form['p_id']
        s_id = request.form['s_id']
        p_name = request.form['p_name']
        city = request.form['city']
        address = request.form['address']
        location = request.form['location']
        p_image = request.form['p_image']
        unit = request.form['unit']
        unit_price = request.form['unit_price']
        qty_stock = request.form['qty_stock']
        qty_sold = request.form['qty_sold']
        availability = request.form['availability']

        # Update the place instance with new values
        if place_edit:
            place_edit.p_id = p_id
            place_edit.s_id = s_id
            place_edit.p_name = p_name
            place_edit.city = city
            place_edit.address = address
            place_edit.location = location
            place_edit.p_image = p_image
            place_edit.unit = unit
            place_edit.unit_price = unit_price
            place_edit.qty_stock = qty_stock
            place_edit.qty_sold = qty_sold
            place_edit.availability = availability

            # Commit the changes to the database
            db.session.commit()

            flash('Place updated successfully!', 'success')
            return redirect(url_for('view_places', s_id=s_id))  # Redirect to the view places page
        else:
            flash('Place not found!', 'danger')
            return redirect(url_for('view_places'))  # Redirect if the place is not found

    # Render the edit places template with the current place details
    if place_edit:
        return render_template('edit_places.html', place_edit=place_edit)
    else:
        flash('Place not found!', 'danger')
        return redirect(url_for('view_places'))  # Redirect if the place is not found

#------------- product ----> delete ----------------#


@app.route('/delete_place/<string:place_id>', methods=['POST'])
def delete_place(place_id):
    # Fetch the place from the database using the place_id
    place_to_delete = places.query.filter_by(p_id=place_id).first()  # Use the correct model name

    if place_to_delete:
        s_id = place_to_delete.s_id  # Store the s_id before deletion
        db.session.delete(place_to_delete)  # Use the ORM method to delete the place
        db.session.commit()  # Commit the changes to the database
        flash('Place deleted successfully!', 'success')
    else:
        flash('Place not found!', 'danger')  # Use 'danger' for error messages
        s_id = None  # Set s_id to None if place not found

    return redirect(url_for('view_places', s_id=s_id))  # Redirect to the places view with s_id  # Redirect to the places view

#------------- product working (ends) ----> create, delete, update  ----------------#

"""# this summary section is bascially showing all the data 
@app.route('/summary')
def summary():
    # fetching all sales records from the database
    sold = sales.query.all()
    return render_template('mgr_summary.html', sold=sold)

@app.route('/mgr_back')
def mgr_back():
     return redirect(url_for('mgr_dashboard'))
"""
"""
@app.route('/summary', methods=['GET'])
def summary():
    # Query total sales
    total_sales = db.session.query(db.func.sum(sales.price)).scalar() or 0

    # Query total number of transactions
    total_transactions = db.session.query(sales).count()

    # Query sales by product
    sales_by_product = db.session.query(
        sales.p_id,
        db.func.sum(sales.price).label('total_sales')
    ).group_by(sales.p_id).all()

    # Prepare summary data
    summary_data = {
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'sales_by_product': [
            {'product_id': product.p_id, 'total_sales': product.total_sales} for product in sales_by_product
        ]
    }

    return jsonify(summary_data) """ # Return the summary as JSON

@app.route('/admin_back')
def admin_back():
     return redirect(url_for('admin_dashboard'))

################################################ MANAGER PAGE FUNCTIONS ENDS ######################################################

################################################ USER PAGE FUNCTIONS START ######################################################


#------------- on user login   ----------------#

@app.route('/user_login')
def user_login():
    return render_template('user_login.html')

#------------- checking the user data and validating ----------------#

@app.route('/user_login_check', methods=['POST'])
def user_login_check():
    # taking the login details from the user login form
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        #query checking weather the user is present in the users table or not
        user = users.query.filter(and_(users.email == email, users.password == password)).first()
        # if user exists then go to dashboard
        if user:  
            session['email'] = user.email # storing the user email for further function
            session['username'] = user.username # as the username is unique storing it
            return redirect(url_for('user_dashboard'))  
    return redirect(url_for('user_login'))


@app.route('/user_dashboard')
def user_dashboard():
    if 'username' in session:
        username = session['username']
    else:
        username = 'Guest'
    # Query the categories data from the database
    states = state.query.all()
    return render_template('user_dashboard.html', username=username, states=states)


#------------- New user registering them ----------------#

@app.route('/user_registration', methods=['POST'])
def user_registration():
    # taking the user details from the form 
    if request.method == 'POST':
        username = request.form['inputAddress']
        name = request.form['inputName']
        email = request.form['inputEmail4']
        password = request.form['inputPassword4']
        address = request.form['inputAddress2']
        gender = request.form['inputGender']
        phone = request.form['inputPhone']

        # Check if the email already exists
        existing_user = users.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # If email does not exist, proceed with registration
        try:
            # storing the new user details in new_user variable 
            new_user = users(username=username, name=name, email=email, password=password, 
                             address=address, gender=gender, phone=phone)
            # adding the user to the database
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('user_login'))
        except IntegrityError:
            db.session.rollback()  # Rollback the session in case of any integrity error
            flash('There was an error registering your account. Please try again.', 'danger')
            return redirect(url_for('register'))
        
    return redirect(url_for('register'))

#------------- displaying all the states in the user dahboard   ----------------#

@app.route('/states')
def states():
    all_states = state.query.all()  # Fetch all states from the database
    return render_template('states.html', states=all_states)


@app.route('/place_detail')
def place_detail():
    place_id = request.args.get('place_id')
    place = places.query.filter_by (p_id=place_id).first()  # Fetch the place by ID
    return render_template('place_detail.html', place=place)

@app.route('/user_view_places')
def user_view_places():
    s_id = request.args.get('s_id')  # Get the state ID from the query string
    places_list = places.query.filter_by(s_id=s_id).all()  # Query all places associated with the state ID

    # Group places by state (or any other category)
    categories = {}
    for place in places_list:
        if place.state.s_name not in categories:
            categories[place.state.s_name] = []
        categories[place.state.s_name].append(place)

    return render_template('user_view_places.html', categories=categories)


#------------- adding items to cart functions begin   ----------------#

"""last_u_id = None         
last_cart_id = None         

@app.route('/u_add_item/<p_id>', methods=['GET', 'POST'])
# get the product based on the p_id
def u_add_item(p_id): 
    # query the product table for data stored against p_id (product id)
    # checking weather the quantity user wants to buy is availabe or not 
    cart_data = places.query.filter_by(p_id=p_id).first()
    # using global variable in function
    global last_u_id
    global last_cart_id

    # when user adds a product from the available products table user specify the quantity purchased by him
    if request.method == 'POST':
        u_id = session['username']
        s_id = request.form['s_id']
        p_id = request.form['p_id']
        qty = int(request.form['qty'])
        unit_price = float(request.form['unit_price'])
        # setting the bill to 0 because the product is added to cart but yet to buy the product 
        bill_no = 0   
        # when user is assing the product , Check if the u_id is different from the last_u_id
        if last_u_id != u_id:

            # If u_id is different then query the cart table to find the max(cart_id) for that u_id
            # user started buy the products but left without buying
            max_cart_id_for_user = cart.query.filter_by(u_id=u_id).with_entities(db.func.max(cart.cart_id)).scalar()
            # query the cart table to find the max(cart_id) for the cart table
            # if the user is a not already present in the cart table and starting a new buying
            max_cart_id_present_in_the_table = cart.query.with_entities(db.func.max(cart.cart_id)).scalar()
            
            if max_cart_id_for_user is None and cart.query.count() == 0:
                # If the user is not present in the cart table and the cart table is empty
                last_cart_id = 1  # setting the cart as 1

            elif max_cart_id_for_user is None: 
                # If the user is not present in the cart table but the cart table is not empty
                # thus the cart table must be having a max(cart_id) for the table 
                last_cart_id = max_cart_id_present_in_the_table + 1 # the max value present in table +1

            else:
                # If the user is present in the cart table and left without buying 
                # came back ro purchase 
                last_cart_id = max_cart_id_for_user   # the max value present in table

            last_u_id = u_id

        # Calculate the price = (quantity X unit_price)
        price = qty * unit_price
        # checking weather the sufficient quantity is present in stock or not.
        if qty <= (cart_data.qty_stock - cart_data.qty_sold):
            # Create a new Cart record as the sufficient quantity is present 
            new_cart_item = cart(u_id=u_id, s_id=s_id, p_id=p_id, qty=qty, unit_price=unit_price, price=price, cart_id=last_cart_id, bill_no=bill_no)
            db.session.add(new_cart_item)  #add it to the database
            db.session.commit()

            # Redirect the user to the dashboard after form submission
            return redirect(url_for('user_dashboard'))
        
        # If the quantity added by user is more than the available stock
        else:
            # here displaying the user what quantity is present in the stock
            flash(f"Only {cart_data.qty_stock - cart_data.qty_sold} units are left in stock.")
            return render_template('u_add_item.html', cart=cart_data)
    return render_template('u_add_item.html', cart=cart_data)
"""
@app.route('/u_add_item/<p_id>', methods=['GET', 'POST'])
def u_add_item(p_id):
    # Get the product based on p_id
    cart_data = places.query.filter_by(p_id=p_id).first()

    if request.method == 'POST':
        u_id = session['username']
        s_id = request.form['s_id']
        p_id = request.form['p_id']
        qty = int(request.form['qty'])
        unit_price = float(request.form['unit_price'])
        bill_no = 0

        # Use session to store last_u_id and last_cart_id instead of globals
        if 'last_u_id' not in session or session['last_u_id'] != u_id:
            session['last_u_id'] = u_id

            # Get max cart_id for the user or set to 1 if no carts exist
            max_cart_id_for_user = cart.query.filter_by(u_id=u_id).with_entities(db.func.max(cart.cart_id)).scalar()
            max_cart_id_present_in_table = cart.query.with_entities(db.func.max(cart.cart_id)).scalar()

            if max_cart_id_for_user is None and cart.query.count() == 0:
                session['last_cart_id'] = 1
            elif max_cart_id_for_user is None:
                session['last_cart_id'] = max_cart_id_present_in_table + 1
            else:
                session['last_cart_id'] = max_cart_id_for_user

        # Calculate price = quantity * unit_price
        price = qty * unit_price

        # Check if sufficient quantity is available in stock
        if qty <= (cart_data.qty_stock - cart_data.qty_sold):
            # Create a new cart item
            new_cart_item = cart(u_id=u_id, s_id=s_id, p_id=p_id, qty=qty, unit_price=unit_price, price=price, 
                                 cart_id=session['last_cart_id'], bill_no=bill_no)
            db.session.add(new_cart_item)
            db.session.commit()

            # Redirect to dashboard after adding item
            return redirect(url_for('cart_view'))

        else:
            # Show flash message if not enough stock is available
            flash(f"Only {cart_data.qty_stock - cart_data.qty_sold} units are left in stock.")
            return render_template('u_add_item.html', cart=cart_data)

    return render_template('u_add_item.html', cart=cart_data)


#------------- adding items to cart functions ends   ----------------#



#------------- viewing the items added in cart  ----------------#


@app.route('/cart_view')
def cart_view():
    # Get the current user's username from the session
    username = session.get('username')     
    # Query the maximum cart_id present in the table for u_id (username).
    max_cart_id = db.session.query(func.max(cart.cart_id)).filter_by(u_id=username).scalar()
    # store the cart id in the session
    session['cart_id'] = max_cart_id  
    # Get the current cart_id from the session
    cart_id = session.get('cart_id')

    # Query the cart items for the current user's cart_id and u_id (username)
    # bascially joining the cart and the product table for displaying the p-name present in product table
    cart_items = (
        db.session.query(cart)
        .join(places, cart.p_id == places.p_id)
        .filter(cart.cart_id == cart_id, cart.u_id == username)
        .all()
    )
    # Load related Product data into each Cart object
    for item in cart_items:
        item.places = item.places
    return render_template('cart.html', cart_items=cart_items)


@app.route('/remove_item/<int:item_id>', methods=['POST'])
def remove_item(item_id):
    # Retrieve the cart item based on the item_id
    cart_item = cart.query.get(item_id)
    if cart_item:
        # Remove the cart item from the database
        db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for('cart_view'))




#------------- viewing the items added in cart ends  ----------------#



@app.route('/buy_cart', methods=['GET', 'POST'])
def buy_cart():
    # Fetch the u_id from the session (assuming it is stored as 'username')
    u_id = session.get('username')

    # Get the last cart ID for the specific user (u_id)
    max_cart_id_for_user = cart.query.filter_by(u_id=u_id).with_entities(db.func.max(cart.cart_id)).scalar()
    last_cart_id = max_cart_id_for_user

    if last_cart_id is not None:
        # Get all cart items for the specific user (u_id) and cart_id
        cart_items = cart.query.filter_by(u_id=u_id, cart_id=last_cart_id).all()

        if cart_items:
            # Check if any items in the cart are out of stock
            items_to_remove = []
            for cart_item in cart_items:
                places_record = places.query.filter_by(s_id=cart_item.s_id, p_id=cart_item.p_id).first()
                if places_record:
                    if cart_item.qty > (places_record.qty_stock - places_record.qty_sold):
                        items_to_remove.append(cart_item)

            if items_to_remove:
                # Remove out of stock items from the cart
                for item in items_to_remove:
                    db.session.delete(item)
                db.session.commit()
                flash(', '.join([f'places {item.places.p_name} went out of stock, removed from your cart!' for item in items_to_remove]), 'warning')

                # Redirect to cart_view with the flashed message
                return redirect(url_for('cart_view'))

            else:
                # Transfer cart data to the sales table and update stock
                for cart_item in cart_items:
                    new_sale = sales(
                        u_id=cart_item.u_id,
                        s_id=cart_item.s_id,
                        p_id=cart_item.p_id,
                        qty=cart_item.qty,
                        unit_price=cart_item.unit_price,
                        price=cart_item.price,
                        cart_id=cart_item.cart_id,
                        # using the generate_bill_number function and storing its return value
                        bill_no=generate_bill_number(),
                        # date and time stored in cart table / time and date when user added the product
                        date_time=cart_item.date_time,
                        # date and time to be stored in sales table / time and date when user bought the product
                        billing_date_time=datetime.utcnow()
                    )
                    db.session.add(new_sale)

                    # Update qty_sold in the product table
                    places_record = places.query.filter_by(s_id=cart_item.s_id, p_id=cart_item.p_id).first()
                    if places_record:
                        places_record.qty_sold += cart_item.qty

                        # Check if the quantity sold is equal to the quantity in stock / it becomes out of stock
                        if places_record.qty_sold >= places_record.qty_stock:
                            # Set availability to "O" ----> 'Out of stock'
                            places_record.availability = 'O'

                    # Apply the changes to the product table
                    db.session.commit()

                # Delete the cart items
                cart.query.filter_by(u_id=u_id, cart_id=last_cart_id).delete()
                # Commit the changes to the cart table
                db.session.commit()

    # Redirect the user to the dashboard after completing the purchasing
    return redirect(url_for('thankyou'))


@app.route('/update_quantity/<int:item_id>', methods=['POST'])
def update_quantity(item_id):
    # Get the new quantity from the form
    new_qty = request.form.get('qty', type=int)

    # Retrieve the cart item based on the item_id
    cart_item = cart.query.get(item_id)
    if cart_item:
        # Update the quantity in the cart
        cart_item.qty = new_qty
        db.session.commit()
        flash("Quantity updated successfully!", "success")
    else:
        flash("Cart item not found.", "danger")

    return redirect(url_for('cart_view'))

def generate_bill_number():
    # using the strftime for converting the buying time to a string format
    # as the date, day, year, time never get repeated in the same order
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    # as its not real date time so put any alphabet to remember that its string like B
    return f"B{timestamp}"






# implementing the search for users if user wants to buy an specific product
# or the user wants to buy from a specific category


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    results = []
    
    if query:
        # Search for states based on state name or state description
        results = state.query.filter(
            or_(
                state.s_name.ilike(f'%{query}%'),
                state.s_description.ilike(f'%{query}%')
            )
        ).all()
    else:
        # If no query, fetch all states
        results = state.query.all()

    return render_template('user_dashboard.html', states=results, search_query=query)


# a back to original dashboard route
@app.route('/back')
def back():
     return redirect(url_for('user_dashboard'))

@app.route('/user_profile')
def user_profile():
    # Assuming the user is logged in and the username is stored in the session
    username = session.get('username')

    # Fetch user data from the database using the username
    user = users.query.filter_by(username=username).first()

    # If user not found, redirect or show an error message
    if not user:
        return "User not found", 404

    # Render the profile page and pass the user data
    return render_template('user_profile.html', user=user)


def get_current_user():
    username = session.get('username')  # Retrieve username from the session
    if username:
        return users.query.filter_by(username=username).first()  # Fetch user details from the DB
    return None  # If the username is not found in session, return None

@app.route('/past_orders')
def past_orders():
    user = get_current_user()
    if not user:  # If the user is not logged in
        return redirect(url_for('login'))  # Redirect to login page

    # Continue with the query and rendering of past orders
    orders = db.session.query(
        sales.bill_no,
        sales.billing_date_time,
        state.s_name.label('state_name'),
        places.p_name.label('place_name'),
        places.p_image.label('place_image')
    ).join(
        state, state.s_id == sales.s_id
    ).join(
        places, places.p_id == sales.p_id
    ).filter(
        sales.u_id == user.username
    ).all()

    return render_template('past_orders.html', orders=orders)

# this summary section is bascially showing all the data 
@app.route('/summary')
def summary():
    # fetching all sales records from the database
    sold = sales.query.all()
    return render_template('mgr_summary.html', sold=sold)

################################################ USER PAGE FUNCTIONS ENDS ######################################################

@app.route('/view360')
def view360():
    return render_template('user_360.html')

@app.route('/register')
def register():
    return render_template('register3.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

