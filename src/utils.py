import time

startup_complete = False


def set_startup_complete(value: bool):
    global startup_complete
    startup_complete = value


def loading_animation():
    animation = "|/-\\"
    idx = 0
    while not startup_complete:
        print(f"\rInitializing {animation[idx % len(animation)]} ", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print("\rInitialization complete!    ")
