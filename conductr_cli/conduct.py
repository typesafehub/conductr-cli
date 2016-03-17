from conductr_cli import main_handler


def main_method():
    from conductr_cli import conduct_main
    conduct_main.run()

if __name__ == '__main__':
    main_handler.run(main_method)
