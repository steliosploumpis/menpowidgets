from collections import Sized
import IPython.display as ipydisplay
import ipywidgets
from mayavi import mlab
import numpy as np
from menpowidgets.style import map_styles_to_hex_colours
from menpowidgets.options import (AnimationOptionsWidget, TextPrintWidget,
                                  SaveMayaviFigureOptionsWidget)
from menpowidgets.tools import LogoWidget
from menpo.shape import PointCloud, ColouredTriMesh, TriMesh


def visualize_used_points(template, w_i_n, colour=(0.2, 0.8, 0.3)):
    colours = np.ones_like(template.points)
    colours[w_i_n, 0] = colour[0]
    colours[w_i_n, 1] = colour[1]
    colours[w_i_n, 2] = colour[2]
    return ColouredTriMesh(template.points, trilist=template.trilist,
                           colours=colours)


def view_landmark_displacement(source, target, renderer, group=None):
    from menpo3d.visualize.viewmayavi import MayaviVectorViewer3d
    source_lms = source.landmarks[group].lms
    target_lms = target.landmarks[group].lms

    source_lms.view(new_figure=False, marker_colour=(1, 1, 0),
                    marker_size=0.03)
    target_lms.view(new_figure=False, marker_colour=(1, 0, 0.5),
                    marker_size=0.03)

    points = source_lms.points
    diff = target_lms.points - source_lms.points
    MayaviVectorViewer3d(figure_id=renderer.figure, new_figure=False,
                         points=points, vectors=diff)
    # mlab.quiver3d(points[:, 0], points[:, 1], points[:, 2],
    #               diff[:, 0], diff[:, 1], diff[:, 2])


def deformation_visualization(current_instance, initial_instance, aligned_mesh,
                              renderer, group=None, w_i_n=None):
    in_landmarks = current_instance.landmarks[group].lms
    #figure = in_landmarks.view(new_figure=False, marker_size=0.03,
    # marker_colour=(0, 0.3, 1))
    if w_i_n is not None:
        colour = (0.2, 0.8, 0.3)
        #coloured_mesh = visualize_used_points(current_instance, w_i_n)
        #coloured_mesh.view(new_figure=False)
        colours = np.ones_like(current_instance.points)
        colours[w_i_n, 0] = colour[0]
        colours[w_i_n, 1] = colour[1]
        colours[w_i_n, 2] = colour[2]
        current_instance = ColouredTriMesh(current_instance.points,
                                           trilist=current_instance.trilist,
                                           colours=colours)
    r = current_instance.view(new_figure=False, figure_id=renderer.figure)
    view_landmark_displacement(initial_instance, aligned_mesh,
                               renderer, group=group)

    # return the colouredtrimesh actor (we need to clear it!)
    return r._actors[0]

def visualize_nicp(nicp_results, source, target, group=None, style='coloured',
                   browser_style='buttons'):
    # Ensure that the code is being run inside a Jupyter kernel!
    from menpowidgets.utils import verify_ipython_and_kernel
    verify_ipython_and_kernel()
    print('Initializing...')

    # Make sure that images is a list even with one image member
    if not isinstance(nicp_results, Sized):
        nicp_results = [nicp_results]

    # Get the number of results
    n_results = len(nicp_results)

    # Define the styling options
    if style == 'coloured':
        logo_style = 'info'
        widget_box_style = 'info'
        widget_border_radius = 10
        widget_border_width = 1
        animation_style = 'info'
        save_figure_style = 'danger'
        info_style = 'info'
    else:
        logo_style = 'minimal'
        widget_box_style = ''
        widget_border_radius = 0
        widget_border_width = 0
        animation_style = 'minimal'
        save_figure_style = 'minimal'
        info_style = 'minimal'

    # Define render function
    def render_function(_):
        # Clear figure
        save_figure_wid.renderer.clear_figure()

        if hasattr(save_figure_wid, '__actor'):
            # manually clear the colourtrimesh for now!
            save_figure_wid.renderer.figure.scene.remove_actors(save_figure_wid.__actor)
            del save_figure_wid.__actor
        # Render instance
        id_ = result_number_wid.selected_values if n_results > 1 else 0
        actor = deformation_visualization(nicp_results[id_][0], source, target,
                                  save_figure_wid.renderer, group=group,
                                  w_i_n=nicp_results[id_][2])
        save_figure_wid.__actor = actor
        update_info(nicp_results[id_][1])

        save_figure_wid.renderer.force_draw()

    # Define function that updates the info text
    def update_info(info):
        text_per_line = [
            "> Stiffness Weight: {}".format(info['alpha']),
            "> Landmark Weight: {}".format(info['beta']),
            "> Omitted {:.2%}".format(info['prop_omitted']),
            "> Normal Error: {:.2%}".format(info['prop_omitted_norms'])
        ]
        info_wid.set_widget_state(text_per_line=text_per_line)

    # Group widgets
    info_wid = TextPrintWidget(text_per_line=[''] * 6, style=info_style)
    save_figure_wid = SaveMayaviFigureOptionsWidget(renderer=None,
                                                    style=save_figure_style)
    if n_results > 1:
        # Result selection slider
        index = {'min': 0, 'max': n_results - 1, 'step': 1, 'index': 0}
        result_number_wid = AnimationOptionsWidget(
            index, render_function=render_function, index_style=browser_style,
            interval=0.5, description='NICP:', loop_enabled=True,
            continuous_update=False, style=animation_style)

        # Header widget
        header_wid = ipywidgets.HBox(
            children=[LogoWidget(style=logo_style), result_number_wid],
            align='start')
    else:
        # Header widget
        header_wid = LogoWidget(style=logo_style)

    options_box = ipywidgets.Tab(children=[info_wid, save_figure_wid])
    tab_titles = ['Info', 'Export']
    for (k, tl) in enumerate(tab_titles):
        options_box.set_title(k, tl)
    wid = ipywidgets.VBox(children=[header_wid, options_box], align='start')
    wid.margin = '0.2cm'

    # Set widget's style
    wid.box_style = widget_box_style
    wid.border_radius = widget_border_radius
    wid.border_width = widget_border_width
    wid.border_color = map_styles_to_hex_colours(widget_box_style)

    # Display final widget
    ipydisplay.display(wid)

    # Trigger initial visualization
    render_function({})
