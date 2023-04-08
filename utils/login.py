import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

file_path = 'credentials.yaml'

if not os.path.isfile(file_path):
    open(file_path, 'w').write("")


def login():
    with open(file_path) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    name, authentication_status, username = authenticator.login('Login', 'main')

    return authentication_status

if __name__ == "__main__":
    hashed_passwords = stauth.Hasher(["111"]).generate()
    print(hashed_passwords)
