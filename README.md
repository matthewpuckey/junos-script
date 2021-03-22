# junos-script

Bare script to perform Junos tasks in parallel; work in progress.

Tested on Python 3.8.5 in Ubuntu Docker image.

## Installation
    
    git clone https://github.com/matthewpuckey/junos-script
    cd junos-script
    pip3 install -r requirements.txt

## Usage examples

Retrieve facts (serial numbers, RE status, hostname, Junos version etc.) from multiple devices listed on command line and print to standard output.
    
    python3 junos_script.py facts --hosts device1.internal:22,device2.internal:830


Retrieve facts from multiple devices listed in CSV with headers "ipaddress" and "port". Write facts back to a different CSV.

If port is not specified, port 22 will be used.

    python3 junos_script.py facts --file devices.csv --hosts ipaddress --ports port --output facts.csv


Perform reboot. 

Be careful rebooting numerous devices at once; you might reboot a device upstream of a device you are also trying to reboot!

Using --delaytime (in minutes) could help, though I would be cautious. If no delay is specified, the script specifies 1 minute anyway.

    python junos_script.py reboot --delaytime 4 --hosts device1.internal:22,device2.internal:830
