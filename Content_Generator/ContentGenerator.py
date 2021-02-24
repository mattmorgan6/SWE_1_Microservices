import sys
import os
from tkinter import *
import tkinter.scrolledtext as st
import wikipedia as wiki
import pika
# import json
import messaging_service


##### FUNCTIONS ####

def generateResults(prim_key=None, secon_key=None) -> str:
    """
    This function takes a primary key and a secondary key and search Wikipedia for a page title
    that matches the primary key, and if found, will search the page's content for a paragraph
    that contains both primary, and secondary key. Then returns the paragraph that contains
    both keywords.

    The function can be used two ways. Keywords can be passed into the function, or if keywords
    are passed through the GUI, the function will get the keyword and use that instead.

    :param prim_key: a str used to search wiki for a page title containing the prim_key
    :param secon_key: a str used to search the prim_key wiki page for a the secon_key
    :return: a string of content that contains both the primary and secondary keywords.
    """

    # Clear text area if it is not empty
    if text_area != "":
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

    # Get the page contents of the primary key
    content = page.content

    # Search the page contents for a paragraph containing both primary and secondary keywords
    results = findParagraph(primary_key, secondary_key, content)
    RabbitMq_send(results)

    # Display the results in the result text box
    text_area.insert(INSERT, results)

    return results


def insertText(body):
    received_text_box.insert(END, body)


def findParagraph(primary_key: str, secondary_key: str, content: str) -> str:
    """
    Finds a paragraph containing both primary and secondary keywords.

    :param primary_key: a string of the primary keyword
    :param secondary_key: a string of the secondary keyword
    :param content: a string of the paragraph found containing both keywords
    :return: a string of the paragraph.
    """

    # Split the primary keyword page by '\n' indicating a new paragraph
    contentByNewLine = content.split('\n')
    foundP_indices = []
    n = 0
    # While loop to find paragraphs containing both keywords and saving the index in foundP_indices
    while n < len(contentByNewLine):
        lineContent = contentByNewLine[n]
        if (primary_key in lineContent) and (secondary_key in lineContent):
            foundP_indices.append(n)
            n += 1
        else:
            n += 1

    # foundP_indices array is empty then that means there does not exist a paragraph where both keywords were used.
    if len(foundP_indices) == 0:
        return "No results, sorry!"

    return contentByNewLine[foundP_indices[0]]


def clearAll():
    """
    A function that clears the primary_keyword entry, secondary_keyword entry, and the results text box.
    :return: None
    """
    pk_entry.delete(0, END)
    sk_entry.delete(0, END)
    text_area.delete("1.0", "end")
    received_text_box.delete("1.0", "end")


def exportResults():
    """
    A function that is used with the 'Export to CSV' button. It creates an output.csv file with the headers, primary,
    keyword, secondary keyword, and the results.
    :return:
    """
    primary_key = pk_entry.get()
    secondary_key = sk_entry.get()
    content = text_area.get("1.0", "end")
    header = "input_keywords, output_content\n"

    with open("output.csv", "w") as wf:
        wf.write(header)
        wf.write(f'{primary_key};{secondary_key},"{content}"\n')

def RabbitMq_send(data):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='channel_1')

    # message = json.dumps(data)

    channel.basic_publish(exchange='', routing_key='channel_1', body=data)
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

# create an entry for primary keyword
pk_entry = Entry(root, width=20)
pk_entry.place(x=131, y=151, width=154, height=27)

# create an entry for secondary keyword
sk_entry = Entry(root, width=20)
sk_entry.place(x=131, y=224, width=154, height=31)

# text box for results with scrollbar
text_area = st.ScrolledText(root, width=31, wrap='word', height=90, font=("Times New Roman", 12), bg="#DADEC5",
                            borderwidth=0)
text_area.pack(padx=74, pady=200, side="right")

# text box for Received with scrollbar
received_text_box = st.ScrolledText(root, width=360, wrap='word', height=90, font=("Times New Roman", 12), bg="#DADEC5",
                            borderwidth=0)
received_text_box.place(x=38, y=410, width=342, height=80)


# ExportCSV button that exports the results into an output.csv file
exportCsvButton = Button(root, image=exportCsvButtonIcon, borderwidth=1, bg="#66AFBE", command=exportResults)
exportCsvButton.place(x=518, y=488, width=148, height=34)

# Generate Button uses the keywords to search wiki for a paragraph
# containing both keywords and display it in the results box
generateButton = Button(root, image=generateButtonIcon, borderwidth=1, bg="#BCD2D6", command=generateResults)
generateButton.place(x=154, y=292, width=109, height=34)

# Start over button clears entry fields as well as results
restartButton = Button(root, image=restartButtonIcon, borderwidth=1, bg="#66AFBE", command=clearAll)
restartButton.place(x=758, y=491, width=43, height=36)


if __name__ == "__main__":


    # Checks if there is a file passed with the python file
    # if there is a file, it will parse the contents, gather the keyword results, and output an output.csv file.

    if len(sys.argv) == 2:

        # Save the filename
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

                # Pass the keywords into the get_results function and save it in the variable keyword_contents
                keyword_contents = generateResults(split_keyword[0], split_keyword[1])

                # Then append the new line into new_content
                new_content.append(f'{line}, "{keyword_contents}\n"')
                index += 1

        # New_content variable has the new format of our output.csv file. We open to write a new file and
        # write each line from new_content to output.csv file
        # with open("output.csv", "w") as wf:
        #     for each in new_content:
        #         wf.write(each)
        RabbitMq_send(new_content)

    # Passing in keywords through the CLI
    elif len(sys.argv) > 2:
        first_keyword = sys.argv[1]
        second_keyword = sys.argv[2]
        results = generateResults(first_keyword, second_keyword)

    else:
        root.mainloop()

