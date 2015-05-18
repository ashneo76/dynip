#!/usr/bin/python
from flask import Flask, request
from flask_debugtoolbar import DebugToolbarExtension
from linode import api as l
from cloudflare import CloudFlare as CF
import os
import yaml

config = yaml.load(open('config.yml'))

app = Flask(__name__)
app.debug = config['DYN_DEBUG'] == '1'
if app.debug:
	app.config['SECRET_KEY'] = config['DYN_DBG_SECRET']
	toolbar = DebugToolbarExtension(app)


@app.route('/update')
def update():
    ip = request.remote_addr
    print('Received new ip: ' + ip)
    status = update_ip(service=config['DYN_SRV_TYPE'],
                       ip=ip,
                       root=config['DYN_DOMAIN'],
                       name=config['DYN_RES'],
                       rec_type=config['DYN_TYPE'])
    if status == -1:
        pass
    return ip


def update_ip(service, ip, root, name, rec_type):
    status = -1
    if service == 'linode':
        status = linode_update_ip(ip, root, name, rec_type)
    elif service == 'cf':
        status = cf_update_ip(ip, root, name, rec_type)

    return status


def linode_update_ip(ip, root, name, rec_type='cname'):
    linode = l.Api(key=config['DYN_LINODE_KEY'])
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
            if r['TYPE'] == rec_type and r['NAME'] == name:
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
                                          type=rec_type,
                                          target=ip)
            status = 0

    return status


def cf_update_ip(ip, root, name, rec_type='cname'):
    status = -1
    service_mode = 1
    if rec_type == 'A' or rec_type == 'AAAA':
        service_mode = 0

    target_name = name + '.' + root
    cf = CF(config['DYN_CF_EMAIL'], config['DYN_CF_KEY'])
    domain_list = cf.rec_load_all(z=root)['response']['recs']['objs']
    create_new = True
    for d in domain_list:
        if d['name'] == target_name:
            cf.rec_edit(z=root, _type=rec_type, _id=d['rec_id'], name=name, content=ip, service_mode=service_mode)
            create_new = False
            status = 0
            break

    if create_new:
        cf.rec_new(zone=root, _type=rec_type, content=ip, name=target_name, service_mode=service_mode)
        status = 0

    return status

if __name__ == '__main__':
    app.run(host='::', port=5000)
