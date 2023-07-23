from Dollhouse.client import Client
import pyuac
import time
import keyboard
import datetime
import schedule


def bootstrap():
    print(f"Operations commenced on {datetime.datetime.now().strftime('%c')}\n")

    mu01 = Client(["sign-in",
                   "logistics",
                   "combat",
                   "intelligence",
                   "exploration",
                   "battery",
                   "home",
                   "logistics"])  # note: next addition will be battle-sim automation

    mu01 = Client(["combat",
                   "simulation"])
    mu01.run()

    print("\n" + "\u2501" * 50 + "\n")


def main():
    print("\n" + "\u2501" * 50 + "\n")
    print(f"\u2728 Program started on {datetime.datetime.now().strftime('%c')} \u2728")
    print("\n" + "\u2501" * 50 + "\n")

    bootstrap()

    # Schedule the program to run every 30 minutes
    schedule.every(30).minutes.do(bootstrap)

    while True:

        if keyboard.is_pressed("ctrl") and keyboard.is_pressed('q'):
            print("Program terminated")
            break

        # Run pending scheduled tasks
        schedule.run_pending()
        time.sleep(0.1)  # sleep for 0.1 second between checks


if __name__ == '__main__':
    if not pyuac.isUserAdmin():
        print("Re-launching as admin!")
        pyuac.runAsAdmin()
    else:
        main()

