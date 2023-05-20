from Dollhouse.client import Client


def main():
    mu01 = Client(port=51332)
    mu01.run()


if __name__ == '__main__':
    main()

