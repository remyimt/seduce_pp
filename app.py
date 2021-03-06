from database.connector import open_session, close_session
from database.tables import User as dbUser
from initialization import login_manager, app, User
from lib.config_loader import load_config
import datetime, flask, flask_login, initialization, logging, logging.config, database.connector


def logging_config():
    logging.config.fileConfig('logging-pifrontend.conf', disable_existing_loggers=1)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)


@login_manager.user_loader
def user_loader(user_email):
    db_session = open_session()
    db_user = db_session.query(dbUser).filter(dbUser.email == user_email).first()
    ret_val = None
    if db_user is not None and db_user.user_authorized:
        user = User()
        user.id = db_user.email
        user.firstname = db_user.firstname
        user.lastname = db_user.lastname
        user.ssh_key = db_user.ssh_key
        user.is_admin = db_user.is_admin
        user.user_authorized = db_user.user_authorized
        ret_val = user
    close_session(db_session)
    return ret_val


@app.template_filter()
def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """
    now = datetime.now()
    diff = now - dt
    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )
    for period, singular, plural in periods:
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)
    return default


if __name__ == '__main__':
    try:
        logging_config()
        port_number = load_config().get('frontend', { 'port': 9000 }).get('port')
        logger = logging.getLogger('APP')
        logger.info('Running on port %s' % port_number)
        app.run(debug=True, port=port_number, host="0.0.0.0")
    except:
        logger.exception('The frontend is crashed:')
