from conductr_cli import main_handler


def main_method():
    from conductr_cli import shazar_main
    shazar_main.run()


def run():
    main_handler.run(main_method)

if __name__ == '__main__':
    run()
