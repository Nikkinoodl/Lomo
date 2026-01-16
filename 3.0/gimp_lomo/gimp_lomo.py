#!/usr/bin/env python3

# --- This text description taken from the original script file. Updates added at bottom ---
#
#   The GIMP -- an image manipulation program
#   Copyright (C) 1995 Spencer Kimball and Peter Mattis
#   
#   This program is free software  you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation  either version 2 of the License, or
#   (at your option) any later version.
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY  without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with this program  if not, write to the Free Software
#   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#  
#   Copyright (C) 2005 Francois Le Lay <mfworx@gmail.com>
#  
#   Version 0.3 - Changed terminology, settings made more user-friendly
#   Version 0.2 - Now using radial blending all-way
#   Version 0.1 - Rectangular Selection Feathering doesn't look too good
#  
#   Usage: 
#  
#   - Vignetting softness: The vignette layer is scaled with a 
#     default size equal to 1.5 the image size. Setting it to 2
#     will make the vignetting softer and going to 1 will make
#     the vignette layer the same size as the image, providing
#     for darker blending in the corners.
#  
#   - Saturation and contrast have default values set to 20 and act 
#     on the base layer.
#  
#   - Double vignetting: when checked this will duplicate the Vignette 
#     layer providing for a stronger vignetting effect.
#  
#   October 23, 2007
#   Script made GIMP 2.4 compatible by Donncha O Caoimh, donncha@inphotos.org
#   Download at http://inphotos.org/gimp-lomo-plugin/
#   Updated by elsamuko <elsamuko@web.de>
#   http://registry.gimp.org/node/7870
#  
#   January 29, 2024
#   Script made 2.10 compatible by Simon Bland portraitsbysimonbland.com
#   Download at https://github.com/Nikkinoodl/Lomo/edit/main/pbsb-lomo.scm
#
#   January 10, 2026
#   Script converted to GIMP 3.0 Python plugin by Simon Bland portraitsbysimonbland.com.
#   Contrast, saturation, lens and blur effects are now done via non-destructive Gegl operations and
#   the order of operations has been changed. Default values and ranges for each have changed.
#
#   Basic vignetting is now provided by the lens distortion effect - its faster and editable.
#
#   As before, double and black vignetting are performed in additional layers however changes have been made to both
#   operations. The strength of the additional vignettes can be modified by changing layer opacity
#   after the plugin is run.
#


'''
A complex GIMP 3 plugin that combines multiple effects to recreate the feel of retro, analog photography. Adapted from
the original version, simplified, converted to Gimp 3 Python and modified to use Gegl operations.
'''

import sys, gi

gi.require_version('Gegl', '0.4')
gi.require_version("Gimp", "3.0")
gi.require_version('GimpUi', '3.0')
gi.require_version('Babl', '0.1')

from gi.repository import Gimp, GLib, Babl, Gegl, GObject, GimpUi

# Set up the color modification options
colorList = [("Neutral", "Neutral"),
            ("Old Red", "Old Red"),
            ("XPro Green", "XPro Green"),
            ("Blue", "Blue"),
            ("XPro Autumn", "XPro Autumn"),
            ("Movie", "Movie"),
            ("Vintage", "Vintage"),
            ("XPro LAB", "XPro LAB"),
            ("Light Blue", "Light Blue"),
            ("Redscale", "Redscale"),
            ("Retro B/W", "Retro B/W"),
            ("Paynes B/W", "Paynes B/W"),
            ("Sepia", "Sepia")
]

# Create Gimp.Choices for color options. Will not work without identifier, index, label and description.
def populate_choice(choice, items):
  for index, (identifier, label) in enumerate(items):
    description = f"Apply {label} effect"
    choice.add(identifier, index, label, description)

Colors = Gimp.Choice.new()
populate_choice(Colors, colorList)

class Lomo(Gimp.PlugIn):
  def do_query_procedures(self):
    return ["lomo"]
	
  def do_create_procedure(self, name):
    Gegl.init(None)
    Babl.init()

    proc = Gimp.ImageProcedure.new(
      self,
      name,
      Gimp.PDBProcType.PLUGIN,
      self.run,
      None
    )
    proc.set_image_types("*")
    proc.set_menu_label("Lomo")
    proc.add_menu_path("<Image>/Filters/Simon")
    proc.set_documentation("Applies multiple effects to recreate the feel of Lomo photography",
                          "Applies multiple effects to the entire visible image to recreate the feel of Lomo photography. " \
                          "Latest version can be downloaded from https://github.com/Nikkinoodl/Lomo/3.0/gimp_lomo/gimp_lomo.py ",
                          name)
    proc.set_attribution("Simon Bland", "copyright Simon Bland", "2026")

    proc.add_double_argument("vignetteSoftness", "Vignette Softness", "Vignette Softness", 0, 50, 35, GObject.ParamFlags.READWRITE)
    proc.add_double_argument("saturation", "Saturation", "Saturation", 1, 2, 1, GObject.ParamFlags.READWRITE)
    proc.add_double_argument("contrast", "Contrast", "Contrast", 1, 2, 1.1, GObject.ParamFlags.READWRITE)
    proc.add_boolean_argument("sharpness", "Sharpness", "Sharpness", True, GObject.ParamFlags.READWRITE)
    proc.add_double_argument("wideAngle", "Wide Angle Distortion", "Wide Angle Distortion", 0, 100, 25, GObject.ParamFlags.READWRITE)
    proc.add_double_argument("lensBlur", "Lens Blur", "Lens Focusing Blur", 0, 10, 3, GObject.ParamFlags.READWRITE)
    proc.add_double_argument("motionBlur", "Motion Blur", "Motion Blur", 0, 20, 12, GObject.ParamFlags.READWRITE)
    proc.add_boolean_argument("grain", "Grain", "Grain", True, GObject.ParamFlags.READWRITE)
    proc.add_choice_argument("colorScheme",
                            "Color Scheme",
                            "The color theme to be applied to the image.",
                            Colors,
                            "Neutral",
                            GObject.ParamFlags.READWRITE)
    proc.add_boolean_argument("invertA", "Invert LAB-A", "Invert LAB-A", True, GObject.ParamFlags.READWRITE)
    proc.add_boolean_argument("invertB", "Invert LAB-B", "Invert LAB-B", True, GObject.ParamFlags.READWRITE)
    proc.add_boolean_argument("dblVignette", "Double Vignette", "Double Vignette", True, GObject.ParamFlags.READWRITE)
    proc.add_boolean_argument("blackVignette", "Black Vignette", "Black Vignette", True, GObject.ParamFlags.READWRITE)
    proc.add_double_argument("aRadius", "Adj Feather (%)", "Adjust Feather Radius (%)", 0.0, 200, 100.0, GObject.ParamFlags.READWRITE)                  

    return proc

  def run(self, procedure, run_mode, image, drawables, config, data):
    Gegl.init(None)
    Babl.init()

    # Get drawable and convert image type if needed
    drawable = drawables[0]
    
    if drawable.is_gray():
      image.convert_rgb()

    # Start an undo group so the whole operation is one step in history, and set
    # foreground and background colors
    image.undo_group_start()
    Gimp.context_push()
    
    # Show a dialog box to capture input parameters
    if run_mode == Gimp.RunMode.INTERACTIVE:
      GimpUi.init('lomo')

      dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
      dialog.fill(['vignetteSoftness',
                  'saturation',
                  'contrast',
                  'sharpness',
                  'wideAngle',
                  'lensBlur',
                  'motionBlur',
                  'grain',
                  'colorScheme',
                  'invertA',
                  'invertB',
                  'dblVignette',
                  'blackVignette',
                  'aRadius'
      ])

      if not dialog.run():
        dialog.destroy()

        Gimp.context_pop()
        image.undo_group_end()

        # Close Gegl
        Gegl.exit()
    
        return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
    
      else:
        dialog.destroy()

    # Get dialog variables
    vignetteSoftness = config.get_property('vignetteSoftness')
    saturation = config.get_property('saturation')
    contrast = config.get_property('contrast')
    sharpness = config.get_property('sharpness')
    wideAngle = config.get_property('wideAngle')
    lensBlur = config.get_property('lensBlur')
    motionBlur = config.get_property('motionBlur')
    grain = config.get_property('grain')
    colorScheme = config.get_property('colorScheme')
    invertA = config.get_property('invertA')
    invertB = config.get_property('invertB')
    dblVignette = config.get_property('dblVignette')
    blackVignette = config.get_property('blackVignette')
    aRadius = config.get_property('aRadius')

    #
    # --- Calculate image dimensions and some common coordinates ---
    #

    Gimp.Selection.all(image)
    sel_size = Gimp.Selection.bounds(image)
    w = sel_size.x2 - sel_size.x1
    h = sel_size.y2 - sel_size.y1

    #set image center
    centerX = w / 2
    centerY = h / 2

    #feather amount for black vignette
    feather = 0.3 * aRadius * (w + h) / 200

    #all gradients are used with zero offset
    offset = 0

    #
    # --- Base layer and effects ----
    #

    self.SetDefaultContexts()

    # Create and insert a new base layer which will be the starting point for the effects
    #baseLayer = Gimp.Layer.new_from_drawable(drawable, image)
    baseLayer = self.AddLayerFromVisible(image, "Base Effects")

    # Add base effects
    self.SetContrast(baseLayer, contrast)
    self.SetSaturation(baseLayer, saturation)
    self.LensDistortion(baseLayer, wideAngle, vignetteSoftness)

    if lensBlur > 0:
      self.GaussianBlur(baseLayer, lensBlur)  # Gaussian blur instead of gegl:lens-blur plugin as it causes Gimp to crash

    if motionBlur > 0:
      self.MotionBlur(baseLayer, motionBlur)  # Focus blur to create fuzziness in the corners and edges of the image

    if sharpness == True:
      self.UnsharpMask(baseLayer)

    #
    # --- Color effects ---
    #

    # Because some color effects duplicate existing layers, it is better to apply these after
    # any distortion or blur effects
    match colorScheme:
      case "Old Red": #rom djinn (http://registry.gimp.org/node/4683)
        baseLayer.curves_spline(Gimp.HistogramChannel.VALUE, [0, 0, 68/255, 64/255, 190/255, 219/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.RED, [0, 0, 39/255, 93/255, 193/255, 147/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.GREEN, [0, 0, 68/255, 70/255, 1.0, 207/255])
        baseLayer.curves_spline(Gimp.HistogramChannel.BLUE, [0, 0, 94/255, 94/255, 255/255, 199/255])

      case "XPro Green": #from lilahpops (http://www.lilahpops.com/cross-processing-with-the-gimp/)
        baseLayer.curves_spline(Gimp.HistogramChannel.RED, [0, 0, 80/255, 84/255, 149/255, 192/255, 191/255, 248/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.GREEN, [0, 0, 70/255, 81/255, 159/255, 220/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.BLUE, [0, 27/255, 1.0, 213/255])

      case "Blue":
        baseLayer.curves_spline(Gimp.HistogramChannel.RED, [0, 62/255, 1.0, 229/255])
        baseLayer.curves_spline(Gimp.HistogramChannel.GREEN, [0, 0, 69/255, 29/255, 193/255, 240/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.BLUE, [0, 27/255, 82/255, 44/255, 202/255, 241/255, 1.0, 1.0])
    
      case "XPro Autumn":
        baseLayer.curves_spline(Gimp.HistogramChannel.RED, [0, 0, 90/255, 150/255, 240/255, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.GREEN, [0, 0, 136/255, 107/255, 240/255, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.BLUE, [0, 0, 136/255, 107/255, 1.0, 246/255])

      case "Movie": #from http://tutorials.lombergar.com/achieve_the_indie_movie_look.html
        baseLayer.curves_spline(Gimp.HistogramChannel.VALUE, [40/255, 0, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.RED, [0, 0, 127/255, 157/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.GREEN, [0, 8/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.BLUE, [0, 0, 127/255, 106/255, 1.0, 245/255])

      case "Vintage": #from mm1 (http://registry.gimp.org/node/1348)
        # Yellow Layer with opacity of 59 in multiply mode
        yellowLayer = self.AddLayer(image, "Yellow", w, h, 59, Gimp.LayerMode.MULTIPLY)
        self.FillWithColor(yellowLayer, 251/255, 242/255, 163/255)

        # Magenta Layer with opacity of 20 in screen mode
        magentaLayer = self.AddLayer(image, "Magenta", w, h, 20, Gimp.LayerMode.SCREEN)
        self.FillWithColor(magentaLayer, 232/255, 101/255, 179/255)

        # Cyan Layer with opacity of 17 in screen mode
        cyanLayer = self.AddLayer(image, "Cyan", w, h, 17, Gimp.LayerMode.SCREEN)
        self.FillWithColor(cyanLayer, 9/255, 73/255, 233/255)

      case "XPro LAB": #LAB from Martin Evening (http://www.photoshopforphotographers.com/pscs2/download/movie-06.pdf)
        # Decompose, stretch levels, and recompose separately for A and B channels. Doing it this way allows the A/B mix
        # to be adjusted.
        drawA = self.AddLayerFromVisible(image, "LAB_A")
        drawB = self.AddLayerFromVisible(image, "LAB_B")
      
        # Decompose image to LAB
        for (draw, layer) in [(drawA, 1), (drawB, 2)]:
          # Decompose and extract decomposed image and layers
          result = self.Decompose(image, draw)
          imgLAB = result.index(1)        
          layersLAB = imgLAB.get_layers()

          # Select the appropriate layer and stretch the levels
          currentLayer = layersLAB[layer]
          currentLayer.levels_stretch()

          # Recompose back to the originating layer and delete the decomposed image
          self.Recompose(imgLAB, currentLayer)
          imgLAB.delete()

          # Fine tune the effect
          self.SetOpacityModeCombo(draw, 40, Gimp.LayerMode.HSL_COLOR)
          self.GaussianBlur(draw)

      case "Light Blue":
        baseLayer.curves_spline(Gimp.HistogramChannel.RED, [0, 0, 154/255, 141/255, 232/255, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.GREEN, [0, 0, 65/255, 48/255, 202/255, 215/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.GREEN, [0, 21/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.BLUE, [0, 0, 68/255, 89/255, 162/255, 206/255, 234/255, 1.0])
        baseLayer.levels(Gimp.HistogramChannel.VALUE, 25/255, 1.0, True, 1.25, 0, 1.0, True)

      case "Redscale":
      # The order of layer operations is important in this scheme
        blueLayer = self.AddLayerFromVisible(image, "Blue Filter")

        filter = Gimp.DrawableFilter.new(baseLayer, "gegl:channel-mixer", "Channel Mixer")
        config = filter.get_config()
        config.set_property('preserve-luminosity', True)
        config.set_property('rr-gain', 1.0)
        config.set_property('rg-gain', 0.0)
        config.set_property('rb-gain', 0.0)
        config.set_property('gr-gain', 0.0)
        config.set_property('gg-gain', 0.0)
        config.set_property('gb-gain', 0.0)
        config.set_property('br-gain', 0.0)
        config.set_property('bg-gain', 0.0)
        config.set_property('bb-gain', 0.0)
        filter.update()
        baseLayer.append_filter(filter)

        self.SetOpacityModeCombo(blueLayer, 40, Gimp.LayerMode.SCREEN)
        self.AddMask(blueLayer, Gimp.AddMaskType.COPY)
        self.FillWithColor(blueLayer, 0, 0, 1.0)
             
        baseLayer.curves_spline(Gimp.HistogramChannel.RED, [0, 0, 127/255, 190/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.GREEN, [0, 0, 127/255, 62/255, 240/255, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.BLUE, [0, 0, 1.0, 0])

      case "Retro B/W":
        baseLayer.desaturate(Gimp.DesaturateMode.LUMINANCE)
        baseLayer.curves_spline(Gimp.HistogramChannel.RED, [0, 15/255, 1.0, 1.0])
        baseLayer.curves_spline(Gimp.HistogramChannel.BLUE, [0, 0, 1.0, 230/255])
        baseLayer.curves_spline(Gimp.HistogramChannel.VALUE, [0, 0, 63/255, 52/255, 191/255, 202/255, 1.0, 1.0])

      case "Paynes B/W":
        baseLayer.desaturate(Gimp.DesaturateMode.LUMINANCE) 
        baseLayer.colorize_hsl(215, 11, 0)

      case "Sepia":
        baseLayer.desaturate(Gimp.DesaturateMode.LUMINANCE) 
        baseLayer.colorize_hsl(30, 25, 0)

    # LAB channel inversion
    for (selected, layer) in [(invertA, 1), (invertB, 2)]:
        if selected == True:
          # Decompose and extract the decomposed image and layers
          result = self.Decompose(image, baseLayer)
          imgLAB = result.index(1)
          layersLAB = imgLAB.get_layers()

          # Get the appropriate layer and invert it
          currentLayer = layersLAB[layer]
          currentLayer.invert(False)
          self.Recompose(imgLAB, currentLayer)

          # Delete the decomposed image
          imgLAB.delete()

    #
    # --- Post colorization and distortion effects ---
    # 

    if grain == True:
      # Add grain after colorization has been applied.
      self.Grain(baseLayer)
    
    if dblVignette == True:
      # For extra vignetting, a new layer with black overlay is created.
      self.SetDefaultContexts()
      vignetteLayer = self.AddLayer(image, "Double Vignette", w, h, 80, Gimp.LayerMode.OVERLAY)
      vignetteLayer.edit_gradient_fill(Gimp.GradientType.RADIAL, offset, False, 1, 0, True, centerX, centerY, 0 , 0)
      self.NoiseSpread(vignetteLayer)

    if blackVignette == True:
       # A fully opaque black vignette (modify opacity to suit)
      self.SetDefaultContexts()
      blkVignetteLayer = self.AddLayer(image, "Black Vignette", w, h)

      image.set_selected_layers([blkVignetteLayer, None])
      Gimp.Selection.none(image)

      #select an ellipse and feather the selection
      delta = 0.05 * (w + h) / 2
      image.select_ellipse(Gimp.ChannelOps.ADD, 0 - delta, 0 - delta, w + (delta * 2), h + (delta * 2))
      Gimp.Selection.feather(image, feather)
      Gimp.Selection.invert(image)

      #add a black fill to the area
      blkVignetteLayer.edit_fill(Gimp.FillType.FOREGROUND)
      Gimp.Selection.none(image)

    # Overexposure is added by default
    self.SetDefaultContexts()

    # Apply as a radial blend from center to corner
    oeLayer = self.AddLayer(image, "Overexposure", w, h, 50, Gimp.LayerMode.OVERLAY)

    Gimp.context_swap_colors()
    Gimp.context_set_gradient_reverse(False)
    oeLayer.edit_gradient_fill(Gimp.GradientType.RADIAL, offset, False, 1, 0, True, centerX, centerY, 0, 0)

    # Apply a noise spread  
    self.NoiseSpread(oeLayer)
  
    # Restore context and close the undo group
    Gimp.displays_flush()
    Gimp.context_pop()
    image.undo_group_end()

    # Clean up Gegl
    Gegl.exit()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

  #
  # --- Methods for Gegl effects and PDB plugins ---
  #
  
  def Decompose(self, image, draw):
    procedure = Gimp.get_pdb().lookup_procedure('plug-in-decompose')
    config = procedure.create_config()
    config.set_property('run-mode', Gimp.RunMode.NONINTERACTIVE)
    config.set_property('image', image)
    config.set_core_object_array('drawables', [draw])
    config.set_property('decompose-type', 'lab')
    config.set_property('layers-mode', True)
    config.set_property('use-registration', False)
    result = procedure.run(config)
    return result
  
  def GaussianBlur(self, draw, radius = 2.5):
    filter = Gimp.DrawableFilter.new(draw, "gegl:gaussian-blur", "Gaussian Blur")
    config = filter.get_config()
    config.set_property('std-dev-x', radius)
    config.set_property('std-dev-y', radius)
    config.set_property('filter', 'auto') #Enum: AUTO
    config.set_property('abyss-policy', 1) #Enum: BLACK
    config.set_property('clip-extent', True) 
    filter.update()
    draw.append_filter(filter)
    return

  def Grain(self, layer):
      # This implementation is applied directly to the image and is a departure from the original Lomo script.
      # (plug-in-hsv-noise 1 img grain-layer 2 0 0 100)
      filter = Gimp.DrawableFilter.new(layer, "gegl:noise-hsv", "Grain")
      config = filter.get_config()
      config.set_property('holdness', 4.0)
      config.set_property('hue-distance', 0.0)
      config.set_property('saturation-distance', 0.0)
      config.set_property('value-distance', 0.30)
      filter.update()
      layer.append_filter(filter)
      return
  
  def LensDistortion(self, layer, wideAngle, vignetteSoftness):
    # Adapted from (plug-in-lens-distortion 1 img draw 0 0 wide_angle 0 9 0)
    # and modified to give better wide angle effect
    filter = Gimp.DrawableFilter.new(layer, "gegl:lens-distortion", "Lens Distortion")
    config = filter.get_config()
    config.set_property('main', wideAngle)
    config.set_property('edge', wideAngle * 0.25)
    config.set_property('zoom', wideAngle * 0.80)
    config.set_property('x-shift', 0.0)
    config.set_property('y-shift', 0.0)
    config.set_property('brighten', vignetteSoftness)
    bgColor = Gegl.Color.new('black')
    bgColor.set_rgba(0.0, 0.0, 0.0, 0.0)
    config.set_property('background', bgColor)
    filter.update()
    layer.append_filter(filter)
    return

  def MotionBlur(self, layer, motionBlur):
      # In place of (plug-in-mblur 1 img draw 2 motion_blur 0 blend_x blend_y)
      filter = Gimp.DrawableFilter.new(layer, "gegl:focus-blur", "Focus Blur")
      config = filter.get_config()
      config.set_property('blur-type', 'lens') #Enum: LENS_BLUR
      config.set_property('blur-radius', motionBlur)
      config.set_property('highlight-factor', 0.35)
      config.set_property('highlight-threshold-low', 0.310)
      config.set_property('highlight-threshold-high', 1.0)
      # All other properties can be defaulted
      filter.update()
      layer.append_filter(filter)
      return  
  
  def NoiseSpread(self, layer):
    # Adapted from (plug-in-spread 1 img vignette 50 50)
    filter = Gimp.DrawableFilter.new(layer, "gegl:noise-spread", "Noise Spread")
    config = filter.get_config()
    config.set_property('amount-x', 50.0)
    config.set_property('amount-y', 50.0)
    filter.update()
    layer.append_filter(filter)
    return
  
  def Recompose(self, image, draw):
    procedure = Gimp.get_pdb().lookup_procedure('plug-in-recompose')
    config = procedure.create_config()
    config.set_property('run-mode', Gimp.RunMode.NONINTERACTIVE)
    config.set_property('image', image)
    config.set_core_object_array('drawables', [draw])
    result = procedure.run(config)
    return result
  
  def SetContrast(self, layer, contrast):
    filter = Gimp.DrawableFilter.new(layer, "gegl:brightness-contrast", "Brightness and Contrast")
    config = filter.get_config()
    config.set_property('contrast', contrast)
    config.set_property('brightness', 0.0)
    filter.update()
    layer.append_filter(filter)
    return

  def SetSaturation(self, layer, saturation):
    filter = Gimp.DrawableFilter.new(layer, "gegl:saturation", "Saturation")
    config = filter.get_config()
    config.set_property('scale', saturation)
    config.set_property('colorspace', 0) # interpolation color space NATIVE
    filter.update()
    layer.append_filter(filter)
    return 

  def UnsharpMask(self, layer):
    # For this effect, the original code has been replaced with Unsharp Mask and
    # the sharpening effect has been moved lower in the stack.
    # It is applied with default values which can be edited after the plugin is run
    filter = Gimp.DrawableFilter.new(layer, "gegl:unsharp-mask", "Unsharp Mask")
    config = filter.get_config()
    config.set_property('std-dev', 2.0)
    config.set_property('scale', 0.0)
    config.set_property('threshold', 0.0)
    filter.update()
    layer.append_filter(filter)
    return

  #
  # --- Utilities ---
  #
	
  #adds a new layer with transparent fill
  def AddLayer(self, image, name, w, h, opacity = 100, mode = Gimp.LayerMode.NORMAL):
    layer = Gimp.Layer.new(image, name, w, h, Gimp.ImageType.RGBA_IMAGE, opacity, mode)
    image.insert_layer(layer, None, -1)
    layer.fill(Gimp.FillType.TRANSPARENT)

    return layer
  
  #adds a new layer from the visible image
  def AddLayerFromVisible(self, image, name):
    layer = Gimp.Layer.new_from_visible(image, image, name)
    image.insert_layer(layer, None, -1)

    return layer

	#adds a layer mask - fill(0) is white, fill(1) is black
  def AddMask(self, layer, fill):
    mask = layer.create_mask(fill)
    layer.add_mask(mask)

    return mask

  #fills a layer with an r/g/b color
  def FillWithColor(self, layer, r, g, b):
    Gegl.init(None)

    bgColor = Gegl.Color.new('white')
    bgColor.set_rgba(r, g, b, 0)
    Gimp.context_set_background(bgColor)
    layer.fill(Gimp.FillType.BACKGROUND)

    Gegl.exit()
    return

  def SetDefaultContexts(self):
    Gegl.init(None)

    Gimp.context_set_opacity(100)
    Gimp.context_set_paint_mode(Gimp.LayerMode.NORMAL)
    Gimp.context_set_gradient_blend_color_space(Gimp.GradientBlendColorSpace.RGB_LINEAR)
    Gimp.context_set_gradient_reverse(True)
    Gimp.context_set_gradient_fg_transparent()

    fgColor = Gegl.Color.new('black')
    bgColor = Gegl.Color.new('white')
    
    Gimp.context_set_foreground(fgColor)
    Gimp.context_set_background(bgColor)
    
    Gegl.exit()
    return

  def SetOpacityModeCombo(self, layer, opacity, mode):
    layer.set_opacity(opacity)
    layer.set_mode(mode)
    return

# Entry point
Gimp.main(Lomo.__gtype__, sys.argv)
