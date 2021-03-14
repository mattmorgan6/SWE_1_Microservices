# SWE_1_Microservices
This is the portfolio assignment for my Software Engineering I class.
This repo holds two Python microservices, the Life Generator (developed by @mattmorgan6) and Content Generator (developed by @jph-cs). <br><br>
Each uses `Tkinter` as the GUI and RabbitMQ's `pika` as the Microservice Messaging Framework.<br><br>
The Life Generator takes an Amazon toy sales .csv file and allows the user to filter by category and sort by review and number of reviews. The Content Generator takes two keywords and from the first keyword's Wikipedia page, finds a Wikipedia paragraph containing the second keyword.<br><br>
Each microservice can run individually or both can run at the same time. When run at the same time, the Life Generator will display product information from Wikipedia when the user selects a toy.

### To run the Content Generator:
    cd Content_Generator
    python ContentGenerator.py

### To run the Life Generator:
    cd Life_Generator
    python toy_service.py
