from database.connector import open_session, close_session
from database.states import progress_forward
from database.tables import Deployment, User
from datetime import datetime
from lib.config_loader import get_cluster_desc
import json, logging, logging.config, os, random, subprocess, sys, time


test_email = 'test@imt-atlantique.fr'
test_deployment_name = 'automatic testing'
pubkey_file = 'ssh_key/test-piseduce.pub'
# Use this environment to only test the NFS boot process
boot_test_environment = 'boot_test'

# Beautiful logger
logging.config.fileConfig('logging-test.conf', disable_existing_loggers=1)
logger = logging.getLogger("TESTING")

def destroy_test_deployment():
    db_session = open_session()
    test_user = db_session.query(User).filter(User.email == test_email).all()
    if len(test_user) == 0:
        raise Exception("No test user in the database. Please create it:\n"
                "INSERT INTO "
                "user(state, email, firstname, lastname, _password, email_confirmed, user_authorized, is_admin) "
                "VALUES('confirmed', '%s', 'Test','Test', "
                "'$2b$12$PJCxhXp6vwLkEm8y2hctVudY/EQCfq2njV0SuFbglZoJMar0FDm6i', 1, 0, 0);" % test_email)
    test_user_id = test_user[0].id
    db_session.query(Deployment).filter(
            Deployment.user_id == test_user_id).filter(Deployment.name == test_deployment_name).delete()
    close_session(db_session)
    time.sleep(2)
    return test_user_id


def reserve_free_nodes(test_user_id, stats, nb_nodes, test_env="tiny_core"):
    db_session = open_session()
    deployments = db_session.query(Deployment).filter(Deployment.state != "destroyed").all()
    used_nodes = [ d.node_name for d in deployments ]
    cluster_desc = get_cluster_desc()
    logger.info("Used nodes: %s" % used_nodes)
    free_nodes = []
    ssh_user_env = None
    shell_env = None
    script_env = None
    if test_env != 'boot_test':
        for env in cluster_desc["environments"].values():
            if env['name'] == test_env:
                ssh_user_env = env['ssh_user']
                shell_env = env['shell']
                script_env = env['script_test']
        if ssh_user_env is None or shell_env is None:
            logger.error("Environment '%s' not found!" % test_env)
            sys.exit(13)
    for server in cluster_desc["nodes"].values():
        if server.get("name") not in used_nodes:
            free_nodes.append({ 'name': server.get("name"), 'ip': server.get('ip'),
                'ssh_user': ssh_user_env, 'shell': shell_env, 'script': script_env, 'env': test_env })
    if len(free_nodes) > nb_nodes:
        selected_nodes = random.sample(free_nodes, nb_nodes)
    else:
        selected_nodes = free_nodes
    process = subprocess.run("cat %s" % pubkey_file, shell=True, check=True,
            stdout=subprocess.PIPE, universal_newlines=True)
    for node in selected_nodes:
        new_deployment = Deployment()
        new_deployment.state = "nfs_boot_conf"
        new_deployment.environment = test_env
        new_deployment.node_name = node['name']
        new_deployment.name = test_deployment_name
        new_deployment.system_size = 200
        new_deployment.system_pwd = "superC9PWD"
        new_deployment.public_key = process.stdout
        new_deployment.init_script = node['script']
        new_deployment.start_date = datetime.utcnow()
        new_deployment.user_id = test_user_id
        db_session.add(new_deployment)
        # Write statistics about deployments
        if test_env in stats:
            if node['name'] not in stats[test_env]:
                stats[test_env][node['name']] = []
        else:
            stats[test_env] = { node['name']: [] }
        stats[test_env][node['name']].append({ 'ip': node['ip'], 'start_date': str(datetime.utcnow()), 
            'states': { 'last_state': '', 'last_date': None }, 'total': 0,
            'ping': False, 'ssh': False, 'init_script': False })
    close_session(db_session)
    return selected_nodes


def state_register(dep, stats):
    state_info = stats[dep.environment][dep.node_name][-1]['states']
    # Remember the start of the new state
    last_state = state_info['last_state']
    last_date = state_info['last_date']
    if dep.updated_at is not None:
        last_change = datetime.strptime(str(dep.updated_at), '%Y-%m-%d %H:%M:%S')
        from_change = (datetime.utcnow() - last_change).total_seconds()
        if dep.state == 'env_check':
            if from_change > 600:
                state_info[last_state] = from_change
                logger.warning("Detected stuck deployment for the node '%s'" %
                        stats[dep.environment][dep.node_name][-1]['ip'])
                return True
        else:
            if from_change > 300:
                state_info[last_state] = from_change
                logger.warning("Detected stuck deployment for the node '%s'" %
                        stats[dep.environment][dep.node_name][-1]['ip'])
                return True
    if last_state != dep.state:
        logger.info("id: %d, state: %s, updated_at: %s" % (dep.id, dep.state, dep.updated_at))
        if len(last_state) > 0:
            enter_date = datetime.strptime(state_info['last_date'], '%Y-%m-%d %H:%M:%S')
            exit_date = datetime.strptime(str(dep.updated_at), '%Y-%m-%d %H:%M:%S')
            state_info[last_state] = (exit_date - enter_date).total_seconds()
        state_info['last_state'] = dep.state
        if dep.updated_at == None:
            state_info['last_date'] = str(dep.start_date)
        else:
            state_info['last_date'] = str(dep.updated_at)
    if dep.state == 'deployed' or (dep.environment == boot_test_environment and dep.state == 'env_copy'):
        start_dep = datetime.strptime(str(dep.start_date), '%Y-%m-%d %H:%M:%S')
        end_dep = datetime.strptime(str(dep.updated_at), '%Y-%m-%d %H:%M:%S')
        stats[dep.environment][dep.node_name][-1]['total'] = (end_dep - start_dep).total_seconds()
        if dep.state != 'deployed':
            dep.state = 'deployed'
        return True
    else:
        return False


def exec_bash(cmd):
    try:
        process = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
        return True
    except:
        return False


def testing_environment(dep_env, file_id, dep_stats, nb_nodes = 2):
    file_summary = 'deployment_results.txt'
    # Nodes with a deployed environment
    success_nodes = 0
    # Nodes with uncompleted environment
    failed_nodes = 0
    # Nodes with a deployed environement which have passed the additional tests
    active_nodes = 0
    inactive_node_ip = []
    logger.info("Destroy older deployments")
    test_user_id = destroy_test_deployment()
    logger.info("Start a new deployment")
    nodes = reserve_free_nodes(test_user_id, dep_stats, nb_nodes, dep_env)
    if len(nodes) == 0:
        logger.error("No available node")
        sys.exit(2)
    logger.info("Waiting the end of deployments")
    deployed_env = []
    db_session = open_session()
    while len(deployed_env) < len(nodes):
        deployments = db_session.query(Deployment).filter(
                Deployment.user_id == test_user_id).filter(Deployment.name == test_deployment_name).all()
        for d in deployments:
            my_state = d.state
            if d.id not in deployed_env:
                if state_register(d, dep_stats):
                    logger.warning("Stop monitoring the node '%s'" % d.node_name)
                    deployed_env.append(d.id)
            if d.state != my_state:
                logger.info("The deployment state has been modified for the node '%s'" % d.node_name)
                db_session.add(d)
        db_session.commit()
        time.sleep(2)
    close_session(db_session)
    if dep_env == boot_test_environment:
        sleep_time = 50
    else:
        sleep_time = 10
    logger.info("Waiting %d seconds before starting additional tests" % sleep_time)
    time.sleep(sleep_time)
    logger.info("Check the deployment of %d nodes: %s" % (len(nodes), [ n['ip'] for n in nodes] ))
    for n in nodes:
        n_stats = dep_stats[n['env']][n['name']][-1]
        if dep_env == boot_test_environment:
            if n_stats['states']['last_state'] == 'env_copy':
                logger.info("%s: Ping connection" % n['ip'])
                n_stats['ping'] = exec_bash('ping -c 1 -w 1 %s' % n['ip'])
                logger.info("%s: SSH connection" % n['ip'])
                n_stats['ssh'] = exec_bash(
                        'ssh -o ConnectTimeout=2 -o StrictHostKeyChecking=no root@%s echo "testing"' % n['ip'])
            if not (n_stats['ping'] and n_stats['ssh']):
                inactive_node_ip.append(n['ip'])
        else:
            if n_stats['states']['last_state'] == 'deployed':
                success_nodes += 1
                logger.info("%s: Ping connection" % n['ip'])
                n_stats['ping'] = exec_bash('ping -c 1 -w 1 %s' % n['ip'])
                logger.info("%s: SSH connection" % n['ip'])
                n_stats['ssh'] = exec_bash('ssh -i ssh_key/test-piseduce -o ConnectTimeout=2 \
                        -o StrictHostKeyChecking=no %s@%s echo "testing"' % 
                        (n['ssh_user'], n['ip']))
                logger.info("%s: Init script execution" % n['ip'])
                n_stats['init_script'] = exec_bash(
                        'ssh -o ConnectTimeout=2 -o StrictHostKeyChecking=no %s@%s ls picsou.txt' % 
                        (n['ssh_user'], n['ip']))
                if n_stats['ping'] and n_stats['ssh'] and n_stats['init_script']:
                    active_nodes += 1
            else:
                failed_nodes += 1
                logger.info("%s is not deployed. Skip the connection tests!" % n['ip'])
    if dep_env == boot_test_environment:
        if len(inactive_node_ip) > 0:
            logger.warning("Inactive detected nodes: %s" % inactive_node_ip)
        else:
            logger.info("All nodes are properly configured!")
    else:
        logger.info("Write the statistics to the '%s'" % file_summary)
        if not os.path.isfile(file_summary):
            with open(file_summary, 'w') as fsum:
                fsum.write('date_environment failed_deployments complete_deployments active_nodes environment_name\n')
        with open(file_summary, 'a') as fsum:
            fsum.write(' %s          %2d                  %2d               %2d      %s\n' %
                    (file_id, failed_nodes, success_nodes, active_nodes, dep_env))


if __name__ == "__main__":
    file_id = datetime.utcnow().strftime("%y_%m_%d_%H_%M")
    file_stats = 'json_test/%s_stats_tests.json' % file_id
    stats_data = {}
    cluster_desc = get_cluster_desc()
    #for env in [ { 'name': boot_test_environment } ]:
    #for env in [ {'name': 'tiny_core'} ]:
    for env in cluster_desc["environments"].values():
        logger.info("Deploying the '%s' environment" % env['name'])
        testing_environment(env['name'], file_id, stats_data, 10)
    logger.info("Destroy older deployments")
    destroy_test_deployment()
    logger.info("Write the detailed statistics to the '%s'" % file_stats)
    with open(file_stats, 'w') as json_file:
        json.dump(stats_data, json_file, indent=4)
