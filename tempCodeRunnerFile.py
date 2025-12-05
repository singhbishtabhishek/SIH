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