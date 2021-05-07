
def read_config_file():
    with open('config.txt', 'r') as config_file:
        config_vars = config_file.read().split('\n')
        client_id = config_vars[0].split()[1]
        client_secret = config_vars[1].split()[1]
        market = config_vars[2].split()[1]

        return client_id, client_secret, market
