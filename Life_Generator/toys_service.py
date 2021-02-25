from sys import argv
import pandas as pd
from tkinter import *
from tkinter import ttk
import json
from messaging_service import Messenger


headers = ["input_item_type", "input_item_category", "input_number_to_generate",
           "output_item_name", "output_item_rating", "output_item_num_reviews"]


def get_arguments():
    """
    Gets the input csv file.
    Returns the filename string if given else None.
    """

    if len(argv) > 2 or len(argv) < 2:
        return None

    return argv[1]


def get_category_name(x):
    """
    Given a string category: ex. "Hobbies > Railway Sets > Rail > Trains"
    Returns the top level category: ex. "Hobbies"
    """
    try:
        return x.split(' > ')[0]
    except:
        return ""


def get_list_of_categories(df):
    """
    Returns a list of categories for the user to choose from.
    Gathered from amazon_category_and_sub_category's root categories.
    """
    categories = set()
    for item in df['amazon_category_and_sub_category']:
        try:
            if item != "":
                categories.add(item)
        except:
            pass

    return list(categories)


def pretty_print(df):
    """
    Print the top 10 items of df in an easy to read format.
    """
    print("uniq_id\t\t     number_of_reviews:  price:      avg_reviews:     name:")
    for i in range(10):
        print(
            f'{df.iloc[i,0]}  {df.iloc[i,5]}  {df.iloc[i,3]}  {df.iloc[i,7]}  {df.iloc[i,1][:35]}')
    print()


def algorithm(df, x, category):
    """
    Performs the sorting algorithm on df.
    1. Sorts df by uniq_id then by num_of reviews.
    2. Selects to x*10, sorts df by uniq_if, then by average_review_rating.
    Returns a results dataframe of size x.
    """
    ndf = df.loc[df['amazon_category_and_sub_category'] == category].copy()
    ndf.sort_values(by="uniq_id", kind='mergesort', inplace=True)
    ndf.sort_values(by="number_of_reviews", ascending=False,
                    kind='mergesort', inplace=True)

    x *= 10

    rdf = ndf[:x].sort_values(
        by="uniq_id", kind='mergesort')  # sort by uniq_id
    rdf.sort_values(by="average_review_rating", ascending=False,
                    kind='mergesort', inplace=True)  # sort by average_review_rating
    rdf = rdf[:x]
    return rdf


def output_csv(df, args):
    """
    Outputs the top x toys to output.csv
    """
    with open('output.csv', 'w') as outfile:
        for header in headers[:-1]:
            outfile.write(f'{header},')
        outfile.write(f'{headers[-1]}\n')

        for i in range(min(len(df.index), int(args["input_number_to_generate"]))):
            outfile.write(
                f'{args["input_item_type"]},{args["input_item_category"]},{args["input_number_to_generate"]},{df.iloc[i,1]},{df.iloc[i,7]},{df.iloc[i,5]}\n')

        print("Output data now in output.csv")


def csv_service():
    """
    Opens file_name csv file to get user inputs,
    runs the algrithm, 
    and outputs to output.csv
    """

    def get_csv_input(file_name):
        """
        Gets the user specifications from input.csv
        """
        obj = {}
        with open(file_name, "r") as infile:
            line = infile.readline()  # discard headers
            items = infile.readline().strip().split(',')
            for i in range(len(items)):
                obj[headers[i]] = items[i]

        return obj

    obj = get_csv_input(input_file_name)
    rdf = algorithm(
        df, int(obj["input_number_to_generate"]), obj["input_item_category"])
    output_csv(rdf, obj)


class GUI():

    def __init__(self, categories: list, df: pd.DataFrame):
        root = Tk()
        root.title("Life Generator")

        def on_generate(*args):
            """
            Takes the top x toys and sets them to string output_var.
            """
            r = []
            rdf = algorithm(df, x.get(), self.categories_var.get())

            content = []
            for i in range(min(x.get(), len(rdf.index))):
                r_str = f'{rdf.iloc[i,1][:30]},   {rdf.iloc[i,7]},   {rdf.iloc[i,5]} reviews\n'
                r.append(r_str)
                content.append(
                    {"name": rdf.iloc[i, 1], "manufacturer": rdf.iloc[i, 2]})

            self.output_var.set(r)
            self.output_var_list = content

            return rdf

        def on_output_csv(*args):
            rdf = on_generate(args)
            obj = {}
            obj["input_item_type"] = "toys"
            obj["input_item_category"] = self.categories_var.get()
            obj["input_number_to_generate"] = x.get()
            output_csv(rdf, obj)

        # def end_messaging():
        #     # messenger.end_threads()
        #     root.destroy()

        def on_toy_selection(param):
            # print(output_listbox.curselection())
            self.wikiLabel_var.set("")
            obj = self.output_var_list[int(param[0])]
            messenger.send(json.dumps(obj))

        def on_recieve_wikipedia(ch, method, properties, body):
            self.wikiLabel_var.set(f'{body.decode("UTF-8")[:1000]}...')


        # mainframe is the GUI frame. Some of this code is from the tkinter docs.
        mainframe = ttk.Frame(root, padding="10 10 10 10")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

        # category_menu is the list component of categories to choose from.
        self.categories_var = StringVar(value='')
        category_menu = ttk.OptionMenu(
            mainframe,
            self.categories_var,
            categories[0],
            *categories)
        category_menu.grid(column=0, row=1, sticky=W)

        # x is the number of items to generate.
        label = ttk.Label(mainframe, text='Number of toys to output:').grid(
            column=1, row=1)
        x = IntVar(value=5)
        x_entry = ttk.Entry(mainframe, width=4, textvariable=x)
        x_entry.grid(column=2, row=1, sticky=(W, E))

        # button calls on_generate() when pressed.
        ttk.Button(mainframe, text="Get Output", command=on_generate).grid(
            column=0, row=2, columnspan=2)

        # button calls on_generate() when pressed.
        ttk.Button(mainframe, text="Output to output.csv", command=on_output_csv).grid(
            column=1, row=2, columnspan=2)

        # output_listbox lists the output.
        self.output_var = StringVar(value=[])
        output_listbox = Listbox(
            mainframe, listvariable=self.output_var, width=74)
        output_listbox.grid(column=0, row=3, columnspan=3)
        output_listbox.bind("<<ListboxSelect>>", lambda e: on_toy_selection(output_listbox.curselection()))

        # x is the number of items to generate.
        self.wikiLabel_var = StringVar(value="")
        ttk.Label(mainframe, textvariable=self.wikiLabel_var, wraplength=500).grid(column=0, row=4, columnspan=4)

        # set the padding for each component to 5.
        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        messenger.set_on_receive(on_recieve_wikipedia)

        # Call on_generate() when enter is pressed.
        root.bind("<Return>", on_generate)
        # root.protocol("WM_DELETE_WINDOW", end_messaging)
        root.mainloop()


# Driver:
print("Starting toy microservice...\n")
    
# get the dataframe and prep the data:
df = pd.read_csv("amazon_co-ecommerce_sample.csv")
df['number_of_reviews'] = (df['number_of_reviews'].str.replace(',', ''))
df['number_of_reviews'] = pd.to_numeric(df['number_of_reviews'])
df['amazon_category_and_sub_category'] = (
    df['amazon_category_and_sub_category'].apply(get_category_name))

# categories is the list for users to filter results by.
categories = get_list_of_categories(df)
categories.sort()

input_file_name = get_arguments()
if input_file_name:
    csv_service()

messenger = Messenger()

# def printMessage(ch, method, properties, body):
#     print(f' YOOOOOO "{body.decode("UTF-8")}" in channel_1')

# messenger.set_on_receive(printMessage)

ui = GUI(categories, df)


messenger.end_threads()
