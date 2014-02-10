from flask import Flask, request
from flask_debugtoolbar import DebugToolbarExtension
from linode import api as l
import os


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'sicritkiy'
toolbar = DebugToolbarExtension(app)


@app.route('/update')
def update():
    ip = request.remote_addr
    print('Received new ip: ' + ip)
    status = update_ip(ip, root=os.environ['DYN_DOMAIN'], name=os.environ['DYN_RES'],
                       type=os.environ['DYN_TYPE'])
    if status == -1:
        pass
    return ip


def update_ip(ip, root, name, type='cname'):
    api_key = os.environ['LINODE_API_KEY']
    linode = l.Api(key=api_key)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0')
