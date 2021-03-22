import sys
import csv
import json
import time
import argparse
import getpass
from concurrent.futures import ThreadPoolExecutor
from jnpr.junos import Device
from jnpr.junos.utils.sw import SW
from jnpr.junos.exception import ConnectError


def get_credentials():
    """Prompt user for SSH credentials"""
    username = input("Username: ")
    password = getpass.getpass()
    return {'username': username, 'password': password}


def parse_csv(filename, host, port):
    """Parse CSV with filename, host header, and port header"""
    list_devices = []
    try:
        with open(filename) as f:
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                # If --port was not specified, it will use port 22
                list_devices.append({"host": row[host], "port": row[port] if port is not None else 22})
        return list_devices
    except FileNotFoundError:
        print("File doesn't exist!")
        sys.exit()
    except KeyError:
        print("Header/field doesn't exist in CSV file. Check again!")
        sys.exit()


def parse_devices(devices):
    """Parse devices from arguments provided"""
    list_devices = []
    indv = devices.split(",")
    for i in indv:
        split = i.split(":")
        list_devices.append({"host": split[0], "port": split[1]})
    return list_devices


def get_facts(device):
    """Connects to Junos devices and retrieves facts"""
    try:
        with Device(host=device.get("host"),
                user=device.get("username"),
                passwd=device.get("password"),
                port=device.get("port")) as dev:
            return json.dumps(dev.facts)
    except ConnectError as err:
        return f"Cannot connect to device: {err}"
    except Exception as err:
        return err
    

def perform_reboot(device):
    """Connects to Junos devices and performs reboot"""
    try:
        with Device(host=device.get("host"),
                user=device.get("username"),
                passwd=device.get("password"),
                port=device.get("port")) as dev:
            sw = SW(dev)
            result = sw.reboot(in_min=int(device.get("delaytime") or 1))
            return f'{device["host"]}:\n {result}'
    except ConnectError as err:
        return f"Cannot connect to device: {err}"
    except Exception as err:
        return err


def perform_concurrency(func, devices):
    """Executes function name passed to it concurrently"""
    with ThreadPoolExecutor() as executor:
        return list(executor.map(func, devices))


def facts_arg(args):
    """All arguments from facts parser"""
    if args.file:
        if args.hosts is None:
            print("No CSV hosts header specified. Use --hosts")
            sys.exit()
        devices = parse_csv(args.file, args.hosts, args.ports)
    else:
        devices = parse_devices(args.hosts)
    credentials = get_credentials()
    for i in devices:
        i['username'] = credentials.get("username")
        i['password'] = credentials.get("password")
    start = time.time()
    print("\nFetching Junos facts...\n")
    results = perform_concurrency(get_facts, devices)
    if args.output:
        fields = []
        dictionary = []
        for i in results:
            try:
                dictionary.append(json.loads(i))
            except ValueError:
                print(f"{i}\n")
                continue
        for i in dictionary:
            for k in i.keys():
                if k not in fields:
                    fields.append(k)
        with open(args.output, 'w', newline='') as f:
            w = csv.DictWriter(f, fields)
            w.writeheader()
            for i in dictionary:
                w.writerow(i)
        print(f"Output written to {args.output}\n")
    else:
        for result in results:
            print(f"{result}\n")    
    end = time.time()
    print(f"Runtime of {end - start:.2f}s")


def reboot_arg(args):
    if args.file:
        if args.hosts is None:
            print("No CSV hosts headers specified. Use --hosts")
            sys.exit()
        devices = parse_csv(args.file, args.host, args.ports)
    else:
        devices = parse_devices(args.hosts)
    credentials = get_credentials()
    for i in devices:
        i['username'] = credentials.get("username")
        i['password'] = credentials.get("password")
        if args.delaytime:
            i['delaytime'] = args.delaytime
    print("\nPerforming reboot...\n")
    results = perform_concurrency(perform_reboot, devices)
    for result in results:
        print(f"{result}\n")    


parser = argparse.ArgumentParser()
common_parser = argparse.ArgumentParser(add_help=False)
common_parser.add_argument("--hosts",
                            help="""Header in CSV file to identify hosts or enter devices with the following syntax: device1.internal:22,device2.internal:830""")
common_parser.add_argument("--file",
                            help="""CSV filename to use as input for hosts. Use with --hosts & --ports to identify headers""")
common_parser.add_argument("--ports",
                            help="Header in CSV file to identify ports")
common_parser.add_argument("--output", 
                            help="""file.csv.
                            Otherwise, it's printed out""")
subparsers = parser.add_subparsers(help="Commands")
facts_parser = subparsers.add_parser("facts", 
                                    help="Retrieve facts",
                                    parents=[common_parser])
reboot_parser = subparsers.add_parser("reboot",
                                    help="Perform reboot",
                                    parents=[common_parser])
reboot_parser.add_argument("--delaytime",
                            help="Delay to perform reboot in minutes e.g. '2'")
facts_parser.set_defaults(func=facts_arg)
reboot_parser.set_defaults(func=reboot_arg)
args = parser.parse_args()
try:
    args.func(args)
except AttributeError:
    print("See '--help'")
