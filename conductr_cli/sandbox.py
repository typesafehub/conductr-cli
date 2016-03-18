from conductr_cli import main_handler


def main_method():
    from conductr_cli import sandbox_main
    sandbox_main.run()


def run():
    main_handler.run(main_method)

if __name__ == '__main__':
    run()
