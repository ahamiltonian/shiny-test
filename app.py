from shiny.express import ui, input, render
import code


ui.input_selectize(
    "var", "Select variable",
    choices=["revenue", "value"]
)

@render.plot
def hist():
    code.plot_data(input.var())