# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
import sys
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import render_template, request, flash, redirect, url_for

from app_config import *
from forms import *
from models import *


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# Filter for seeking_talent field
def format_boolean_field(boolean):
    if boolean is None:
        return False
    else:
        return True


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues_query = Venue.query.all()

    venues_array = []

    for venue in venues_query:
        venue_dictionary = next((item for item in venues_array
                                 if item["city"] == venue.city and item["state"] == venue.state), None)
        venue_dictionary_index = next((i for i, item in enumerate(venues_array)
                                       if item["city"] == venue.city and item["state"] == venue.state), None)

        upcoming_shows = db.session.query(Show) \
            .filter(Show.venue_id == venue.id and venue.shows.start_time > datetime.utcnow()).all()

        if venue_dictionary is None:

            new_venue = {
                "city": venue.city,
                "state": venue.state,
                "venues": [{
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": len(upcoming_shows),
                }]
            }

            venues_array.append(new_venue)
        else:
            new_venue = {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(upcoming_shows),
            }
            venue_dictionary["venues"].append(new_venue)

            venues_array[venue_dictionary_index] = venue_dictionary

    return render_template('pages/venues.html', areas=venues_array)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')

    venues_query = db.session.query(Venue).filter(Venue.name.ilike("%" + search_term + "%")).all()

    venues_array = []
    for venue in venues_query:
        upcoming_shows = db.session.query(Show) \
            .filter(Show.venue_id == venue.id, Show.start_time > datetime.utcnow()).all()

        new_venue = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(upcoming_shows),
        }
        venues_array.append(new_venue)

    response = {
        "count": len(venues_array),
        "data": venues_array
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Filtering using a query instead of the lambda filter.  Reduces the number of items that are returned.
    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    venue_dictionary = {}

    # The for loops are necessary in order to put the start_time in a string format
    upcoming_shows = db.session.query(Show) \
        .filter(Show.venue_id == venue.id, Show.start_time > datetime.utcnow()).all()

    upcoming_shows_list = []
    for show in upcoming_shows:
        data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist_show.name,
            "artist_image_link": show.artist_show.image_link,
            "start_time": f"{show.start_time}"
        }

        upcoming_shows_list.append(data)

    past_shows = db.session.query(Show) \
        .filter(Show.venue_id == venue.id, Show.start_time < datetime.utcnow()).all()

    past_shows_list = []
    for show in past_shows:
        data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist_show.name,
            "artist_image_link": show.artist_show.image_link,
            "start_time": f"{show.start_time}"
        }

        past_shows_list.append(data)

    venue_object = {
        "id": venue.id,
        "name": venue.name,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "upcoming_shows": upcoming_shows_list,
        "upcoming_shows_count": len(upcoming_shows),
        "past_shows": past_shows_list,
        "past_shows_count": len(past_shows)
    }

    # The below categories are optional and therefore checked for NoneType before updating to the dictionary
    if venue.genres is not None:
        venue_object.update({"genres": venue.genres})
    if venue.website is not None:
        venue_object.update({"website": venue.website})
    if venue.seeking_description is not None:
        venue_object.update({"seeking_description": venue.seeking_description})

    venue_dictionary.update(venue_object)

    return render_template('pages/show_venue.html', venue=venue_dictionary)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form_input = request.form

    error = False
    try:
        max_id = db.session.query(db.func.max(Venue.id)).scalar()
        new_venue = Venue(
            id=1 if max_id is None else max_id + 1,
            name=form_input.get("name"),
            city=form_input.get("city"),
            state=form_input.get("state"),
            address=form_input.get("address"),
            phone=form_input.get("phone"),
            website=form_input.get("website"),
            genres=form_input.getlist("genres"),
            facebook_link=form_input.get("facebook_link"),
            image_link=form_input.get("image_link"),
            seeking_talent=format_boolean_field(form_input.get("seeking_talent")),
            seeking_description=form_input.get("seeking_description")
        )
        db.session.add(new_venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    else:
        flash('An error occurred. Venue ' + form_input.get("name") + ' could not be listed.')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

    venue_query = db.session.query(Venue).filter(Venue.id == venue_id).first()
    try:
        db.session.delete(venue_query)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artist_query = Artist.query.all()

    artist_list = []
    for artist in artist_query:
        artist_object = {
            "id": artist.id,
            "name": artist.name,
        }

        artist_list.append(artist_object)

    return render_template('pages/artists.html', artists=artist_list)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')

    artists_query = db.session.query(Artist).filter(Artist.name.ilike("%" + search_term + "%")).all()

    artists_array = []
    for artist in artists_query:
        upcoming_shows = db.session.query(Show) \
            .filter(Show.artist_id == artist.id, Show.start_time > datetime.utcnow()).all()

        new_artist = {
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(upcoming_shows),
        }
        artists_array.append(new_artist)

    response = {
        "count": len(artists_array),
        "data": artists_array
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = db.session.query(Artist).filter(Artist.id == artist_id).first()

    upcoming_shows = db.session.query(Show) \
        .filter(Show.artist_id == artist.id, Show.start_time > datetime.utcnow()).all()

    upcoming_shows_list = []
    for show in upcoming_shows:
        data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue_show.name,
            "venue_image_link": show.venue_show.image_link,
            "start_time": f"{show.start_time}"
        }

        upcoming_shows_list.append(data)

    past_shows = db.session.query(Show) \
        .filter(Show.artist_id == artist.id, Show.start_time < datetime.utcnow()).all()

    past_shows_list = []
    for show in past_shows:
        data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue_show.name,
            "venue_image_link": show.venue_show.image_link,
            "start_time": f"{show.start_time}"
        }

        past_shows_list.append(data)

    artist_dictionary = {}

    artist_object = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link,
        "upcoming_shows": upcoming_shows_list,
        "upcoming_shows_count": len(upcoming_shows_list),
        "past_shows": past_shows_list,
        "past_shows_count": len(past_shows_list)
    }

    artist_dictionary.update(artist_object)

    return render_template('pages/show_artist.html', artist=artist_dictionary)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_query = db.session.query(Artist).filter(Artist.id == artist_id).first()

    artist = {
        "id": artist_query.id,
        "name": artist_query.name,
        "genres": artist_query.genres,
        "city": artist_query.city,
        "state": artist_query.state,
        "phone": artist_query.phone,
        "website": artist_query.website,
        "facebook_link": artist_query.facebook_link,
        "seeking_venue": artist_query.seeking_venue,
        "seeking_description": artist_query.seeking_description,
        "image_link": artist_query.image_link
    }

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
    edited_artist = request.form
    error = False
    try:
        artist.name = edited_artist.get("name")
        artist.city = edited_artist.get("city")
        artist.state = edited_artist.get("state")
        artist.genres = edited_artist.getlist("genres")
        artist.phone = edited_artist.get("phone")
        artist.website = edited_artist.get("website")
        artist.facebook_link = edited_artist.get("facebook_link")
        artist.seeking_venue = edited_artist.get("seeking_venue")
        artist.seeking_description = edited_artist.get("seeking_description")
        artist.image_link = edited_artist.get("image_link")
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error is False:
        flash('Artist ' + edited_artist.get("name") + ' was successfully changed!')
    else:
        flash('An error occurred. Artist ' + edited_artist.get("name") + ' could not be changed.')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue_query = db.session.query(Venue).filter(Venue.id == venue_id).first()

    venue = {
        "id": venue_query.id,
        "name": venue_query.name,
        "genres": venue_query.genres,
        "address": venue_query.address,
        "city": venue_query.city,
        "state": venue_query.state,
        "phone": venue_query.phone,
        "website": venue_query.website,
        "facebook_link": venue_query.facebook_link,
        "seeking_talent": venue_query.seeking_talent,
        "seeking_description": venue_query.seeking_description,
        "image_link": venue_query.image_link
    }

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    edited_venue = request.form
    error = False
    try:
        venue.name = edited_venue.get("name")
        venue.city = edited_venue.get("city")
        venue.state = edited_venue.get("state")
        venue.address = edited_venue.get("address")
        venue.phone = edited_venue.get("phone")
        venue.website = edited_venue.get("website")
        venue.genres = edited_venue.getlist("genres")
        venue.facebook_link = edited_venue.get("facebook_link")
        venue.image_link = edited_venue.get("image_link")
        venue.seeking_talent = format_boolean_field(edited_venue.get("seeking_talent"))
        venue.seeking_description = edited_venue.get("seeking_description")
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error is False:
        flash('Venue ' + edited_venue.get("name") + ' was successfully listed!')
    else:
        flash('An error occurred. Venue ' + edited_venue.get("name") + ' could not be listed.')
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form_input = request.form

    error = False
    try:
        max_id = db.session.query(db.func.max(Artist.id)).scalar()
        new_artist = Artist(
            id=1 if max_id is None else max_id + 1,
            name=form_input.get("name"),
            city=form_input.get("city"),
            state=form_input.get("state"),
            phone=form_input.get("phone"),
            website=form_input.get("website"),
            genres=form_input.getlist("genres"),
            facebook_link=form_input.get("facebook_link"),
            image_link=form_input.get("image_link"),
            seeking_venue=format_boolean_field(form_input.get("seeking_talent")),
            seeking_description=form_input.get("seeking_description")
        )
        db.session.add(new_artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error is False:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    else:
        flash('An error occurred. Artist ' + form_input.get("name") + ' could not be listed.')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    show_query = Show.query.all()

    shows_list = []
    for show in show_query:
        data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue_show.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist_show.name,
            "artist_image_link": show.artist_show.image_link,
            "start_time": f"{show.start_time}"
        }

        shows_list.append(data)

    return render_template('pages/shows.html', shows=shows_list)


@app.route('/shows/create')
def create_shows():
    artist = db.session.query(Artist).all()
    venue = db.session.query(Venue).all()
    form = ShowForm()
    form.artist_id.choices = [(a.id, a.name) for a in artist]
    form.venue_id.choices = [(v.id, v.name) for v in venue]
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form_input = request.form
    error = False
    try:
        max_id = db.session.query(db.func.max(Show.id)).scalar()
        new_show = Show(
            id=1 if max_id is None else max_id + 1,
            venue_id=form_input.get("venue_id"),
            artist_id=form_input.get("artist_id"),
            start_time=form_input.get("start_time")
        )
        db.session.add(new_show)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
        error = True
    finally:
        db.session.close()
    if error is False:
        flash('Show was successfully listed!')
    else:
        flash('An error occurred. Show could not be listed.')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
