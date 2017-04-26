"""Get all gateways from the Meshify API."""
import meshify


def main():
    """Run the main function."""
    gateways = meshify.query_meshify_api("gateways")
    with open("gateways.json", 'wb') as jsonfile:
        json.dump(gateways, jsonfile, indent=4, sort_keys=True)
    csv_string = "Gateway,ipaddress,url\n"
    for g in gateways:
        csv_string += "{},,\n".format(g['name'])

    with open("gateways.csv", 'wb') as csvfile:
        csvfile.write(csv_string)

if __name__ == '__main__':
    main()
