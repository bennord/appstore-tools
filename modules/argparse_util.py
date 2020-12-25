import argparse


def parseCommandLine():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging.')
    auth_group = parser.add_argument_group(
        title='authentication',
        description='Authentication details are configured (and can be copied from) AppStore Connect->Users & Access->Keys.')
    auth_group.add_argument('--issuer-id', required=True,
                            help='Issuer ID.')
    auth_group.add_argument('--key-id', required=True,
                            help='Key ID.')
    key_group = auth_group.add_mutually_exclusive_group(required=True)
    key_group.add_argument('--key',
                           help='Private Key as a string.')
    key_group.add_argument('--key-file', type=argparse.FileType('r'),
                           help='Private Key from a filepath.')
    return parser.parse_args()
