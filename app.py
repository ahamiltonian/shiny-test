from shiny.express import ui, input, render
import code


ui.input_selectize(
    "var", "Select variable",
    choices=[   "Total Municipal Taxes", 
                "Total Property Value",
                "Population",
                "Municipal Taxes per Capita"]
)

@render.plot
def hist():
    code.plot_data(input.var())