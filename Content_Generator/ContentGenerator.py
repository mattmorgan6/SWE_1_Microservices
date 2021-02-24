import sys
import os
from tkinter import *
import tkinter.scrolledtext as st
import wikipedia as wiki
import pika
import messaging_service as ms

##### FUNCTIONS ####


def generate_results(prim_key=None, secon_key=None) -> str:
    """
    Searches for a Wikipedia page with the primary_key, finds a paragraph containing
    both the primary_key and second_key, display results in the GUI, and return the
    results. 

    :param prim_key: a str used for the main Wikipedia page. 
    :param secon_key: a str used to find a paragraph containing both the primary and secondary keys
    :return: a string of content that contains both the primary and secondary keywords.
    """

    # Clear text area if it is not empty
    text_area.delete("1.0", "end")

    # If no arguments are passed, that means the GUI is being used
    if prim_key is None and secon_key is None:
        primary_key = pk_entry.get()
        secondary_key = sk_entry.get()
    else:
        primary_key = prim_key
        secondary_key = secon_key

    # Exceptions handler for page errors.
    try:
        page = wiki.WikipediaPage(primary_key)
    except (wiki.exceptions.PageError, wiki.exceptions.DisambiguationError) as err:
        text_area.insert(INSERT, err)
        return "Sorry, there was an Error!"

    content = page.content

    # Search the page contents for a paragraph containing both primary and secondary keywords
    results = find_paragraph(primary_key, secondary_key, content)

    # Send results to queue in channel_2
    rmq_send(results)

    # Display the results in the result text box
    text_area.insert(INSERT, results)

    return results


def insert_recv_data():
    """
    Retrive the consumed message from the queue.
    """

    clear_all()
    data = ms.get_recv_data()

    if data != None:
        pk = data[0]
        sk = data[1]
        pk_entry.insert(0, pk)
        sk_entry.insert(0, sk)
        generate_results(pk, sk)
        received_text_box.insert(INSERT, data)
        ms.clr_recv_data()
    else:
        received_text_box.insert(INSERT, "No data")


def find_paragraph(primary_key: str, secondary_key: str, content: str) -> str:
    """
    Finds a paragraph containing both primary and secondary keywords.

    :param primary_key: a str
    :param secondary_key: a str
    :param content: a str
    :return: a string of the paragraph.
    """

    # Split the primary keyword page by '\n' indicating a new paragraph
    content_by_newline = content.split('\n')
    found_indices = []
    index = 0
    # Find paragraphs containing both keywords and saving the index in found_indices
    while index < len(content_by_newline):
        line_content = content_by_newline[index]
        if (primary_key in line_content) and (secondary_key in line_content):
            found_indices.append(index)
            index += 1
        else:
            index += 1

    # Empty variable length contains no matching content
    if len(found_indices) == 0:
        return "No results, sorry!"

    return content_by_newline[found_indices[0]]


def clear_all():
    """
    A function that clears the primary_keyword entry, 
    secondary_keyword entry, the receiving text box,
    and the results text box.
    :return: None
    """
    pk_entry.delete(0, END)
    sk_entry.delete(0, END)
    text_area.delete("1.0", "end")
    received_text_box.delete("1.0", "end")


def export_results():
    """
    A function that is used with the 'Export to CSV' button. 
    It creates an output.csv file with the headers, primary,
    keyword, secondary keyword, and the results.
    :return: None
    """
    primary_key = pk_entry.get()
    secondary_key = sk_entry.get()
    content = text_area.get("1.0", "end")
    header = "input_keywords, output_content\n"

    with open("output.csv", "w") as wf:
        wf.write(header)
        wf.write(f'{primary_key};{secondary_key},"{content}"\n')


def rmq_send(data):
    """
    Send data to the queue.
    :param: data: a str
    :return: None
    """
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='channel_2')
    channel.basic_publish(exchange='', routing_key='channel_2', body=data)
    print(" [x] Sent %r " % data)
    connection.close()


########## TKinter Portion ##############

root = Tk()
root.title('Content Generator')
root.geometry("800x533")
root.resizable(0, 0)

# define the images
bg = PhotoImage(file='./images/background@2x.png')
exportCsvButtonIcon = PhotoImage(file='images/ExportCSV-Button@2x.png')
generateButtonIcon = PhotoImage(file='images/Generate-Button@2x.png')
restartButtonIcon = PhotoImage(file='images/slice1@2x.png')
receivingMessageIcon = PhotoImage(file='images/ReceivingMessage@2x.png')

# create a label
my_background = Label(root, image=bg)
my_background.place(x=0, y=0, relwidth=1, relheight=1)

# create an entry box for primary keyword
pk_entry = Entry(root, width=20)
pk_entry.place(x=131, y=151, width=154, height=27)

# create an entry box for secondary keyword
sk_entry = Entry(root, width=20)
sk_entry.place(x=131, y=224, width=154, height=31)

# a button to show received data and display results
get_recv_button = Button(root, text="Get Data",
                         borderwidth=1, bg="red", command=insert_recv_data)
get_recv_button.place(x=151, y=384.7, width=50, heigh=14)

# text box for results with scrollbar
text_area = st.ScrolledText(root, width=31, wrap='word', height=90, font=("Times New Roman", 12), bg="#DADEC5",
                            borderwidth=0)
text_area.pack(padx=74, pady=200, side="right")

# text box for Received with scrollbar
received_text_box = st.ScrolledText(root, width=360, wrap='word', height=90, font=("Times New Roman", 12), bg="#DADEC5",
                                    borderwidth=0)
received_text_box.place(x=38, y=410, width=342, height=80)


# A button that exports the results into an output.csv file
exportCsvButton = Button(root, image=exportCsvButtonIcon,
                         borderwidth=1, bg="#66AFBE", command=export_results)
exportCsvButton.place(x=518, y=488, width=148, height=34)

# A button that activates the generate_results command and return results.
generateButton = Button(root, image=generateButtonIcon,
                        borderwidth=1, bg="#BCD2D6", command=generate_results)
generateButton.place(x=154, y=292, width=109, height=34)

# Reset button clears entry fields as well as results
restartButton = Button(root, image=restartButtonIcon,
                       borderwidth=1, bg="#66AFBE", command=clear_all)
restartButton.place(x=758, y=491, width=43, height=36)


if __name__ == "__main__":

    # Checks if there is a file passed with the python file
    # if there is a file, it will parse the contents,
    # gather the keyword results, and output an output.csv file.

    if len(sys.argv) == 2:

        filename = sys.argv[1]

        # Open the file split the content by lines into the variable content
        with open(filename) as f:
            content = f.read().splitlines()

        # Variable to save the results and used later for outputting into a csv file.
        new_content = []
        index = 0
        for line in content:
            if index == 0:
                # Header line
                new_content.append(f"{line}, output_content\n")
                index += 1
            else:
                # Split the keywords based on a semicolon
                split_keyword = line.split(';')

                # Pass the keywords into the get_results function and save it in the variable
                keyword_contents = generate_results(
                    split_keyword[0], split_keyword[1])

                # Append the new line into new_content
                new_content.append(f'{line}, "{keyword_contents}\n"')
                index += 1

       # Send the data to the messaging queue
        rmq_send(new_content)

    # Passing in keywords through the CLI
    elif len(sys.argv) > 2:
        first_keyword = sys.argv[1]
        second_keyword = sys.argv[2]
        results = generate_results(first_keyword, second_keyword)

    else:
        messenger = ms.Messenger()
        root.mainloop()
        messenger.end_threads()
