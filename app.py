from flask import Flask, request
from flask_debugtoolbar import DebugToolbarExtension
from linode import api as l
from cloudflare import CloudFlare as CF
import os


app = Flask(__name__)
app.debug = False
app.config['SECRET_KEY'] = 'sicritkiy'
toolbar = DebugToolbarExtension(app)


@app.route('/update')
def update():
    ip = request.remote_addr
    print('Received new ip: ' + ip)
    status = update_ip(service=os.environ['DYN_SRV_TYPE'],
                       ip=ip,
                       root=os.environ['DYN_DOMAIN'],
                       name=os.environ['DYN_RES'],
                       type=os.environ['DYN_TYPE'])
    if status == -1:
        pass
    return ip


def update_ip(service, ip, root, name, type):
    status = -1
    if service == 'linode':
        status = linode_update_ip(ip, root, name, type)
    elif service == 'cf':
        status = cf_update_ip(ip, root, name, type)

    return status


def linode_update_ip(ip, root, name, type='cname'):
    linode = l.Api(key=os.environ['DYN_LINODE_KEY'])
    domain_id = -1
    domain_list = linode.domain_list()
    for d in domain_list:
        if d['DOMAIN'] == root:
            domain_id = d['DOMAINID']

    status = -1
    if domain_id != -1:
        # found a domain_id
        res = linode.domain_resource_list(domainid=domain_id)
        found = False
        resource_id = -1
        for r in res:
            if r['TYPE'] == type and r['NAME'] == name:
                found = True
                resource_id = r['RESOURCEID']
                break

        if found and resource_id != -1:
            linode.domain_resource_update(domainid=domain_id,
                                          resourceid=resource_id,
                                          target=ip)
            status = 0
        else:
            linode.domain_resource_create(domainid=domain_id,
                                          name=name,
                                          type=type,
                                          target=ip)
            status = 0

    return status


def cf_update_ip(ip, root, name, type='cname'):
    status = -1
    target_name = name + '.' + root
    cf = CF(os.environ['DYN_CF_EMAIL'], os.environ['DYN_CF_KEY'])
    domain_list = cf.rec_load_all(z=root)['response']['recs']['objs']
    create_new = True
    for d in domain_list:
        if d['name'] == target_name:
            cf.rec_edit(z=root, _id=d['rec_id'], content=ip)
            create_new = False
            status = 0
            break

    if create_new:
        cf.rec_new(zone=root, _type=type, content=ip, name=target_name, service_mode=0)
        status = 0

    return status

if __name__ == '__main__':
    app.run(host='0.0.0.0')
