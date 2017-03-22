from conductr_cli import bndl_main, main_handler


def main_method():
    bndl_main.run()


def run():
    main_handler.run(main_method)


if __name__ == '__main__':
    run()
