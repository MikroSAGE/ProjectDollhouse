from Dollhouse.client import Client


def main():
    mu01 = Client(["sign-in", "logistics"])
    mu01.run()


if __name__ == '__main__':
    main()

