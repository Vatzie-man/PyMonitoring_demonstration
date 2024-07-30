from db_items import (
    get_options,
    get_option_filter,
    add_item,
    update_item,
    delete_item
)

def main() -> None:
    options_dict: dict = dict()
    options = get_options()
    for x in range(len(options)):
        options_dict[options[x].option] = options[x].state

    print(options_dict)

    # add_item("non", 0)
    # update_item(str, int)
    # delete_item(str)

if __name__ == '__main__':
    main()
