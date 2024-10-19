#!/usr/bin/python3

import requests
import os
import json
import sys
import datetime

base_url="https://wpscan.com/api/v3/"
api_rotation=1
#data_dir="/var/lib/wp-scripts/"
data_dir='/tmp/'
vulnerabilites = []

def wpscan_query(endpoint):
    global api_rotation
   
    file_path = data_dir + endpoint.replace('/', '_') + '.json'
    
    # There is no need to perfrom API request if last sync was within last 12 hours
    if os.path.exists(file_path):
        mod_time = os.path.getmtime(file_path)
        mod_time = datetime.datetime.fromtimestamp(mod_time)
        time_diff = datetime.datetime.now() - mod_time

        if time_diff < datetime.timedelta(hours=12):
            return file_path

    api_key=os.environ.get("WPSCAN_API_" + str(api_rotation))
    
    if api_key == None:
        print("Error: run out of API keys")
        sys.exit(1)

    headers = {'Authorization': 'Token token=' + api_key}
    response = requests.get(base_url + endpoint, headers=headers)
    

    if response.text == '{"status":"rate limit hit"}':
        api_rotation = api_rotation + 1
        wpscan_query(endpoint) # I think that recursion is not right
    
    else:
        with open(file_path, 'w') as json_file:
            json_file.write(response.text)

    return file_path

def version_split(version, length):
    if version == None:
        version = []
        while len(version) < length:
            version.append(0)
        return version

    version = [int(x) for x in version.split('.')]

    while len(version) < length:
        version.append(0)

    return version

def vuln_version(fixed_in, introduced_in, current, version_len=3):
    fixed_in = version_split(fixed_in, version_len)
    introduced_in = version_split(introduced_in, version_len)
    current = version_split(current, version_len)
   
    if current >= fixed_in or current < introduced_in:
        return False
    else:
        return True

def core_check(version):
    req_version=version.replace('.', '')

    file_path = wpscan_query('wordpresses/' + req_version)
    with open (file_path) as json_file:
        vulns = json.load(json_file)[version]["vulnerabilities"]
        for vuln in vulns:
            vuln['slug'] = 'wordpress_' + version
            vuln['component'] = 'core' 
            vuln['customer'] = customer
            vuln['site_url'] = site_url
            vuln['server_type'] = server_type
            vulnerabilites.append(json.dumps(vuln))


def plugin_check(slug, version):
    file_path = wpscan_query('plugins/' + slug)
    
    with open (file_path) as json_file:
        try:
            vulns = json.load(json_file)[slug]["vulnerabilities"]
            for vuln in vulns:
                if vuln_version(vuln['fixed_in'], vuln['introduced_in'], version) == True:
                    vuln['slug'] = slug
                    vuln['component'] = 'plugin'
                    vuln['customer'] = customer
                    vuln['site_url'] = site_url
                    vuln['server_type'] = server_type
                    vulnerabilites.append(json.dumps(vuln))
        except KeyError as e:
            pass # Plugin not found

def theme_check(slug, version):
    file_path = wpscan_query('themes/' + slug)
    with open (file_path) as json_file:
        vulns = json.load(json_file)[slug]["vulnerabilities"]
        for vuln in vulns:
            if vuln_version(vuln['fixed_in'], vuln['introduced_in'], version) == True:
                vuln['slug'] = slug
                vuln['component'] = 'theme'
                vuln['customer'] = customer
                vuln['site_url'] = site_url
                vuln['server_type'] = server_type
                vulnerabilites.append(json.dumps(vuln))

def parse_inventory(file_path):
    with open (file_path) as json_file:
        data = json.load(json_file)
        version = data['wordpress_version']
        plugins = data['plugins']

        global customer
        global site_url
        global server_type
        
        customer = data['customer']
        site_url = data['site_url']
        server_type = data['server']
        
        core_check(version)

        for plugin in plugins:
            if plugin['status'] == 'active':
                plugin_check(plugin['name'], plugin['version'])
    

def generate_output(vulnerabilites):
    print('{"vulnerabilities":[', end='')
    
    for vuln in vulnerabilites:
        if vuln == vulnerabilites[-1]:
            print(vuln, end='')
        else:
            print(vuln + ',', end='')
        
    print(']}')
 
#core_check("4.9.4")
#plugin_check("advanced-custom-fields-pro", "5.12.6")
#theme_check("betheme", '25')

file_path = sys.argv[1]
parse_inventory(file_path)
generate_output(vulnerabilites)
