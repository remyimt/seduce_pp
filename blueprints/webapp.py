from database.connector import open_session, close_session
from database.states import select_process
from database.tables import Deployment, User
from flask import Blueprint
from flask_login import current_user
from glob import glob
from lib.admin_decorators import admin_login_required
from lib.config_loader import get_cluster_desc, load_cluster_desc
import datetime, flask, flask_login, json, random, shutil, string, subprocess


webapp_blueprint = Blueprint('app', __name__, template_folder='templates')

def new_password(stringLength=8):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


@webapp_blueprint.route("/server/take/<string:server_info>")
@flask_login.login_required
def take(server_info):
    """ Create deployments in the initialized state """
    cluster_desc = get_cluster_desc()
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    # Delete previous deployments still in initialized state
    old_dep = db_session.query(Deployment).filter_by(user_id=db_user.id, state="initialized").delete()
    # Reserve the nodes to avoid other users to take them
    info = server_info.split(";")
    server_ids = info[0].split(",")
    server_names = info[1].replace(' ','').split(",")
    for n_name in server_names:
        new_deployment = Deployment()
        new_deployment.process = "deploy"
        new_deployment.state = "initialized"
        new_deployment.node_name = n_name
        new_deployment.user_id = db_user.id
        new_deployment.name = "initialized"
        db_session.add(new_deployment)
    close_session(db_session)
    # Reload the cluster decription to add new environments
    load_cluster_desc()
    return flask.render_template("form_take.html.jinja2",
                                 server_ids=server_ids,
                                 server_names=server_names,
                                 environments=[env 
                                     for env in cluster_desc["environments"].values() if env['type'] != 'hidden'])


@webapp_blueprint.route("/server/process_take/", methods=["POST"])
@flask_login.login_required
def process_take():
    """ Start deploying the selected environment """
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    deployments = db_session.query(Deployment).filter_by(user_id = db_user.id, state = "initialized").all()
    for d in deployments:
        d.name = flask.request.form.get("name")
        d.public_key = flask.request.form.get("public_key")
        d.init_script = flask.request.form.get("init_script")
        pwd = flask.request.form.get("sys_pwd").strip()
        if pwd:
            d.system_pwd = pwd[:50]
        else:
            d.system_pwd = new_password()
        d.environment = flask.request.form.get("environment")
        d.os_update = flask.request.form.get("os_update") == "on"
        d.duration = flask.request.form.get("duration_text")
        d.system_size = flask.request.form.get("more_space")
        d.start_date = datetime.datetime.now()
        d.state = select_process('deploy', d.environment)[0]
    close_session(db_session)
    return flask.redirect(flask.url_for("app.home"))


@webapp_blueprint.route("/server/cancel/")
@flask_login.login_required
def cancel():
    """ Cancel the deployment (that is in the initialized state) """
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    # Delete previous deployments still in initialized state
    old_dep = db_session.query(Deployment).filter_by(user_id=db_user.id, state="initialized").delete()
    close_session(db_session)
    return flask.redirect(flask.url_for("app.resources"))


@webapp_blueprint.route("/server/reboot/<string:n_name>")
@flask_login.login_required
def ask_reboot(n_name):
    """ Hard reboot the server """
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    # Verify the node belongs to my deployments
    my_deployment = db_session.query(Deployment).filter_by(user_id = db_user.id,
            node_name = n_name).filter(Deployment.state != "destroyed").first()
    if my_deployment is not None:
        # Do not remember the 'lost' state but the state before it
        if my_deployment.state != 'lost':
            my_deployment.temp_info = my_deployment.state
        my_deployment.process = "reboot"
        my_deployment.state = select_process("reboot", my_deployment.environment)[0]
    close_session(db_session)
    return flask.redirect(flask.url_for("app.home"))


@webapp_blueprint.route("/server/redeploy/<string:n_name>")
@flask_login.login_required
def ask_redeploy(n_name):
    """ Deploy again the environment on the server """
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    # Verify the node belongs to my deployments
    my_deployment = db_session.query(Deployment).filter_by(user_id = db_user.id,
            node_name = n_name).filter(Deployment.state != "destroyed").first()
    my_deployment.process = "deploy"
    my_deployment.state = select_process("deploy", my_deployment.environment)[0]
    close_session(db_session)
    return flask.redirect(flask.url_for("app.home"))


@webapp_blueprint.route("/server/release/<string:n_name>")
@flask_login.login_required
def ask_release_node(n_name):
    """ Delete the deployment associated to the server """
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    # Get the deployment associated to the node
    my_deployment = db_session.query(Deployment).filter_by(user_id = db_user.id,
            node_name = n_name).filter(Deployment.state != "destroyed").first()
    if my_deployment is not None:
        my_deployment.process = 'destroy'
        my_deployment.state = select_process('destroy', my_deployment.environment)[0]
    close_session(db_session)
    return flask.redirect(flask.url_for("app.home"))


@webapp_blueprint.route("/deployment/destroy/<string:deployment_ids>")
@flask_login.login_required
def ask_destruction(deployment_ids):
    """ Destroy multiple deployments from their id """
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    for d in deployment_ids.split(","):
        deployment = db_session.query(Deployment).filter_by(id = d, user_id = db_user.id).first()
        if deployment is not None:
            deployment.process = 'destroy'
            deployment.state = select_process('destroy', deployment.environment)[0]
    close_session(db_session)
    return flask.redirect(flask.url_for("app.home"))


@webapp_blueprint.route("/server/save_env/<string:n_name>")
@flask_login.login_required
def save_env(n_name):
    """ Display the form to configure the 'save environment' action """
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    deployment = db_session.query(Deployment).filter_by(user_id = db_user.id, node_name = n_name).filter(
            Deployment.state != "destroyed").first()
    env_name = deployment.environment
    close_session(db_session)
    return flask.render_template("form_save_env.html.jinja2",
                                 environment=env_name,
                                 node_name=n_name)


@webapp_blueprint.route("/server/build_env/", methods=["POST"])
@flask_login.login_required
def build_env():
    """ Execute the 'save environment' action => create a file image from the internal storage of the server"""
    cluster_desc = get_cluster_desc()
    db_session = open_session()
    db_user = db_session.query(User).filter_by(email = current_user.id).first()
    deployment = db_session.query(Deployment).filter_by(user_id = db_user.id,
            node_name=flask.request.form.get('node_name')).filter(Deployment.state != "destroyed").first()
    env = cluster_desc['environments'][deployment.environment]
    env['name'] = flask.request.form.get("user_env_name")
    env['img_name'] = env['name'] + '.img.gz'
    user_ssh_user = flask.request.form.get("user_ssh_user")
    if len(user_ssh_user) > 0:
        env['ssh_user'] = user_ssh_user
    env['type'] = 'user'
    env_file_path = cluster_desc['env_cfg_dir'] + env['name'].replace(' ', '_') + '.json'
    with open(env_file_path, 'w') as jsonfile:
        json.dump(env, jsonfile)
    deployment.process = 'save_env'
    deployment.state = 'img_part'
    deployment.temp_info = env['name']
    close_session(db_session)
    return flask.redirect(flask.url_for("app.home"))


@webapp_blueprint.route("/user/ssh_put/", methods=["POST"])
@flask_login.login_required
def ssh_put():
    """ Create/update the SSH key of the user account """
    my_ssh = flask.request.form.get("ssh_key")
    if my_ssh is not None and len(my_ssh) > 0:
        db_session = open_session()
        db_user = db_session.query(User).filter_by(email = current_user.id).first()
        db_user.ssh_key = my_ssh
        close_session(db_session)
    return flask.redirect(flask.url_for("app.user"))


@webapp_blueprint.route("/user/pwd_put/", methods=["POST"])
@flask_login.login_required
def pwd_put():
    """ Create/update the password of the user account """
    pwd = flask.request.form.get("password")
    confirm_pwd = flask.request.form.get("confirm_password")
    if pwd == confirm_pwd:
        db_session = open_session()
        db_user = db_session.query(User).filter_by(email = current_user.id).first()
        db_user._set_password = pwd
        close_session(db_session)
        return flask.redirect(flask.url_for("app.user"))
    else:
        return 'The two passwords are not identical!<a href="/user">Try again</a>'


@webapp_blueprint.route("/")
@flask_login.login_required
def home():
    """ Display the home page that is the deployments page """
    return flask.render_template("deployments.html.jinja2")


@webapp_blueprint.route("/resources")
@flask_login.login_required
def resources():
    """ Display the resources page to select the ressources and create deployments """
    return flask.render_template("resources.html.jinja2")


@webapp_blueprint.route("/deployments")
@flask_login.login_required
def deployments():
    """ Display the deployments page to manage the existing deployments """
    return flask.render_template("deployments.html.jinja2")


@webapp_blueprint.route("/user")
@flask_login.login_required
def user():
    """ Display the user page to register one SSH key, update the password, etc. """
    return flask.render_template("user_vuejs.html.jinja2")


@webapp_blueprint.route("/admin")
@admin_login_required
def admin():
    """ Display the admin page to configure the switches of the cluster and manage user accounts """
    load_cluster_desc()
    return flask.render_template("admin.html.jinja2")


@webapp_blueprint.route("/form_switch")
@flask_login.login_required
def add_switch():
    """ Display the form to add a new switch to the infrastructure """
    return flask.render_template("form_switch.html.jinja2")
