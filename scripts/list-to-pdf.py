#! /usr/bin/env python
# USAGE SYNTAX:
#  list-to-pdf.py [list-id]

# DEPENDENCIES:
#  * Reportlab toolkit

import sys
from trellonos import Trello
from trellonos import FILTER_OPEN
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def starting_cursor_position():
    """ Start drawing at the top left margin """
    return inch, inch * 10

if __name__ == "__main__":
    # Access the Trello API
    trello = Trello.from_environment_vars()

    # Retrieve the list to print
    list_id = sys.argv[1]
    list_object = trello.get_list(list_id)

    # Retrieve the cards in the list
    card_objects = trello.get_cards(list_object, card_filter=FILTER_OPEN)

    # Open a canvas for printing
    pdf_canvas = canvas.Canvas('list.pdf', (8.5 * inch, 11 * inch))

    # Draw the name of the list at the top of the page
    x, y = starting_cursor_position()
    y -= 36
    pdf_canvas.setFont("Helvetica-Bold", 36)
    pdf_canvas.drawString(x, y, list_object['name'])

    # Start drawing cards below that
    x += inch / 2
    y -= inch / 2
    pdf_canvas.setFont("Helvetica", 16)

    for card_object in card_objects:
        pdf_canvas.drawString(x, y, card_object['name'])
        y -= 24

        if y < inch:
            pdf_canvas.showPage()
            temp, y = starting_cursor_position()
            pdf_canvas.setFont("Helvetica", 16)

    pdf_canvas.showPage()

    # Save the PDF we've generated
    pdf_canvas.save()
