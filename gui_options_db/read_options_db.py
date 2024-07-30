from PyMonitoring.gui_options_db.db_items import get_options

def get_opt():
    options_dict: dict = dict()
    options = get_options()
    for x in range(len(options)):
        options_dict[options[x].option] = options[x].state

    return options_dict

def main() -> None:

    out = get_opt()
    print(out)

if __name__ == '__main__':
    main()




